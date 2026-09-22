extends Node

signal state_changed(state: StringName)

const DialogueState = preload("res://scripts/dialogue/dialogue_state.gd")
const NpcRegistry = preload("res://scripts/dialogue/npc_registry.gd")

@export var dialogue_url := "http://127.0.0.1:8000/api/v1/dialogue"
@export_range(0.1, 60.0, 0.1) var timeout_seconds := 15.0

@onready var _http_request: HTTPRequest = $HTTPRequest

var state: StringName = DialogueState.IDLE
var latest_reply := ""
var latest_trace_id := ""
var latest_status := ""

var _state_model := DialogueState.new()
var _npc_registry := NpcRegistry.new()
var _active_npc_id := NpcRegistry.DEFAULT_NPC_ID
var _conversation_id := ""
var _frozen_payload_json := ""
var _frozen_message := ""
var _frozen_display_message := ""
var _frozen_action_kind := "dialogue"
var _frozen_success_display := ""
var _generation := 0
var _request_in_flight := false
var _retry_allowed := false
var _request_sender := Callable()
var _active_completion := Callable()
var _sessions: Dictionary = {}


func _init() -> void:
	_ensure_session(_active_npc_id)
	_restore_active_session()


func _ready() -> void:
	_http_request.timeout = timeout_seconds
	_http_request.max_redirects = 0


func set_request_sender_for_testing(sender: Callable) -> void:
	_request_sender = sender


func active_npc_id() -> String:
	return _active_npc_id


func active_display_name() -> String:
	return _npc_registry.display_name_for(_active_npc_id)


func conversation_id() -> String:
	return _conversation_id


func history() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var session: Dictionary = _sessions.get(_active_npc_id, {})
	for turn: Dictionary in session.get("history", []):
		result.append(turn.duplicate(true))
	return result


func session_count() -> int:
	return _sessions.size()


func conversation_id_for(npc_id: String) -> String:
	if not _sessions.has(npc_id):
		return ""
	return String((_sessions[npc_id] as Dictionary).get("conversation_id", ""))


func switch_npc(npc_id: String) -> bool:
	if not _npc_registry.is_allowed(npc_id):
		return false
	if npc_id == _active_npc_id:
		return true
	if _request_in_flight:
		return false
	_sync_active_session()
	_generation += 1
	_active_npc_id = npc_id
	_ensure_session(npc_id)
	_restore_active_session()
	state_changed.emit(state)
	return true


func begin_send(
	message: String,
	display_message := "",
	action_kind := "dialogue",
	success_display := "",
) -> bool:
	if _request_in_flight:
		return false
	var normalized := message.strip_edges()
	var normalized_display := display_message.strip_edges()
	if normalized_display.is_empty():
		normalized_display = normalized
	if normalized.is_empty() or normalized.length() > 1000:
		_clear_retry_context()
		_set_state(DialogueState.VALIDATION)
		return false

	var payload := {
		"request_id": _generate_uuid(),
		"player_id": "local_player",
		"npc_id": _active_npc_id,
		"conversation_id": _conversation_id,
		"message": normalized,
	}
	_frozen_payload_json = JSON.stringify(payload)
	_frozen_message = normalized
	_frozen_display_message = normalized_display
	_frozen_action_kind = action_kind.strip_edges() if not action_kind.strip_edges().is_empty() else "dialogue"
	_frozen_success_display = success_display.strip_edges()
	return _dispatch(false)


func retry() -> bool:
	if _request_in_flight or not can_retry():
		return false
	return _dispatch(true)


func notify_input_changed(message: String) -> void:
	if _request_in_flight or _frozen_payload_json.is_empty():
		return
	if message.strip_edges() != _frozen_message:
		_clear_retry_context()
		_set_state(DialogueState.IDLE)


func is_request_in_flight() -> bool:
	return _request_in_flight


func can_retry() -> bool:
	return _retry_allowed and not _frozen_payload_json.is_empty() and not _request_in_flight


func active_generation() -> int:
	return _generation


func latest_request_id() -> String:
	if _frozen_payload_json.is_empty():
		return ""
	var payload: Dictionary = JSON.parse_string(_frozen_payload_json)
	return String(payload.get("request_id", ""))


func handle_response(
	generation: int,
	result: int,
	response_code: int,
	body: PackedByteArray,
	headers: PackedStringArray = PackedStringArray(["Content-Type: application/json"]),
) -> void:
	if not _request_in_flight or generation != _generation:
		return
	_request_in_flight = false

	var frozen_payload: Dictionary = JSON.parse_string(_frozen_payload_json)
	var outcome: Dictionary = _state_model.result_for_response(
		result,
		response_code,
		body,
		String(frozen_payload["request_id"]),
		String(frozen_payload["conversation_id"]),
		String(frozen_payload["npc_id"]),
		headers,
	)
	latest_reply = String(outcome["reply"])
	latest_trace_id = String(outcome["trace_id"])
	latest_status = String(outcome["status"])
	_retry_allowed = bool(outcome["retryable"])
	if outcome["state"] == DialogueState.SUCCESS:
		var visible_reply := (
			_frozen_success_display
			if not _frozen_success_display.is_empty() and latest_status != "degraded"
			else latest_reply
		)
		_append_history(
			_frozen_display_message,
			visible_reply,
			latest_status == "degraded",
			_frozen_action_kind,
		)
	_set_state(outcome["state"])


func _dispatch(is_retry: bool) -> bool:
	_generation += 1
	_request_in_flight = true
	_retry_allowed = false
	latest_reply = ""
	latest_trace_id = ""
	latest_status = ""
	_set_state(DialogueState.RETRYING if is_retry else DialogueState.LOADING)

	var headers := PackedStringArray(["Content-Type: application/json"])
	var dispatch_error: int
	if _request_sender.is_valid():
		dispatch_error = int(
			_request_sender.call(
				dialogue_url,
				headers,
				HTTPClient.METHOD_POST,
				_frozen_payload_json,
			)
		)
	elif is_instance_valid(_http_request):
		_active_completion = _on_request_completed.bind(_generation)
		_http_request.request_completed.connect(_active_completion, CONNECT_ONE_SHOT)
		dispatch_error = _http_request.request(
			dialogue_url,
			headers,
			HTTPClient.METHOD_POST,
			_frozen_payload_json,
		)
		if dispatch_error != OK:
			_disconnect_active_completion()
	else:
		dispatch_error = ERR_UNCONFIGURED

	if dispatch_error != OK:
		_request_in_flight = false
		_retry_allowed = true
		_set_state(DialogueState.UNAVAILABLE)
		return false
	return true


func _on_request_completed(
	result: int,
	response_code: int,
	headers: PackedStringArray,
	body: PackedByteArray,
	generation: int,
) -> void:
	_active_completion = Callable()
	handle_response(generation, result, response_code, body, headers)


func _clear_retry_context() -> void:
	_retry_allowed = false
	_frozen_payload_json = ""
	_frozen_message = ""
	_frozen_display_message = ""
	_frozen_action_kind = "dialogue"
	_frozen_success_display = ""


func _disconnect_active_completion() -> void:
	if (
		_active_completion.is_valid()
		and is_instance_valid(_http_request)
		and _http_request.request_completed.is_connected(_active_completion)
	):
		_http_request.request_completed.disconnect(_active_completion)
	_active_completion = Callable()


func _set_state(next_state: StringName) -> void:
	state = next_state
	_sync_active_session()
	state_changed.emit(state)


func _ensure_session(npc_id: String) -> void:
	if _sessions.has(npc_id):
		return
	_sessions[npc_id] = {
		"conversation_id": _generate_uuid(),
		"history": [],
		"frozen_payload_json": "",
		"frozen_message": "",
		"frozen_display_message": "",
		"frozen_action_kind": "dialogue",
		"frozen_success_display": "",
		"state": DialogueState.IDLE,
		"latest_reply": "",
		"latest_trace_id": "",
		"latest_status": "",
		"retry_allowed": false,
	}


func _sync_active_session() -> void:
	_ensure_session(_active_npc_id)
	var session: Dictionary = _sessions[_active_npc_id]
	session["conversation_id"] = _conversation_id
	session["frozen_payload_json"] = _frozen_payload_json
	session["frozen_message"] = _frozen_message
	session["frozen_display_message"] = _frozen_display_message
	session["frozen_action_kind"] = _frozen_action_kind
	session["frozen_success_display"] = _frozen_success_display
	session["state"] = state
	session["latest_reply"] = latest_reply
	session["latest_trace_id"] = latest_trace_id
	session["latest_status"] = latest_status
	session["retry_allowed"] = _retry_allowed
	_sessions[_active_npc_id] = session


func _restore_active_session() -> void:
	var session: Dictionary = _sessions[_active_npc_id]
	_conversation_id = String(session["conversation_id"])
	_frozen_payload_json = String(session["frozen_payload_json"])
	_frozen_message = String(session["frozen_message"])
	_frozen_display_message = String(session["frozen_display_message"])
	_frozen_action_kind = String(session["frozen_action_kind"])
	_frozen_success_display = String(session["frozen_success_display"])
	state = StringName(session["state"])
	latest_reply = String(session["latest_reply"])
	latest_trace_id = String(session["latest_trace_id"])
	latest_status = String(session["latest_status"])
	_retry_allowed = bool(session["retry_allowed"])


func _append_history(message: String, reply: String, degraded: bool, action_kind: String) -> void:
	var session: Dictionary = _sessions[_active_npc_id]
	var turns: Array = session.get("history", [])
	turns.append(
		{
			"message": message,
			"reply": reply,
			"degraded": degraded,
			"action_kind": action_kind,
		}
	)
	while turns.size() > 6:
		turns.pop_front()
	session["history"] = turns
	_sessions[_active_npc_id] = session


func _generate_uuid() -> String:
	var bytes := Crypto.new().generate_random_bytes(16)
	bytes[6] = (bytes[6] & 0x0f) | 0x40
	bytes[8] = (bytes[8] & 0x3f) | 0x80
	var encoded := ""
	for index in range(bytes.size()):
		if index in [4, 6, 8, 10]:
			encoded += "-"
		encoded += "%02x" % bytes[index]
	return encoded
