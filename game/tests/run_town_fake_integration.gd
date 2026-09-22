extends SceneTree

const TOWN_SCENE_PATH := "res://scenes/town.tscn"
const DEADLINE_MILLISECONDS := 18000
const NPCS := [
	{"npc_id": &"neon_guide", "display_name": "Nia"},
	{"npc_id": &"signal_archivist", "display_name": "Ivo"},
	{"npc_id": &"night_courier", "display_name": "Rhea"},
]

var _town: TownScene
var _dialogue: Node
var _relationship: Node
var _input: LineEdit
var _send: Button
var _status: Label
var _history: RichTextLabel
var _conversation_ids: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed := load(TOWN_SCENE_PATH) as PackedScene
	if packed == null:
		_fail("town scene could not be loaded")
		return
	_town = packed.instantiate() as TownScene
	root.add_child(_town)
	await process_frame
	_dialogue = _town.dialogue_client_for_testing()
	_relationship = _town.relationship_client_for_testing()
	var base_url := _base_url_argument()
	_dialogue.dialogue_url = base_url + "/api/v1/dialogue"
	_relationship.relationship_url = base_url + "/api/v1/relationships"
	_input = _town.find_child("MessageInput", true, false) as LineEdit
	_send = _town.find_child("SendButton", true, false) as Button
	_status = _town.find_child("DialogueStatus", true, false) as Label
	_history = _town.find_child("ConversationHistory", true, false) as RichTextLabel
	if _input == null or _send == null or _status == null or _history == null:
		_fail("town dialogue controls were not available")
		return
	_town.set_backend_available_for_testing(true)

	for npc: Dictionary in NPCS:
		if not _town.open_dialogue_for_testing(npc["npc_id"]):
			_fail("approved NPC did not open: %s" % npc["display_name"])
			return
		var conversation_id: String = _dialogue.conversation_id()
		if _conversation_ids.has(conversation_id):
			_fail("different NPCs shared a conversation id")
			return
		_conversation_ids[conversation_id] = String(npc["npc_id"])
		_input.text = "只属于%s的离线测试。" % npc["display_name"]
		_input.text_changed.emit(_input.text)
		_send.pressed.emit()
		if not await _wait_for_dialogue_state(&"success"):
			return
		if (
			_dialogue.active_npc_id() != String(npc["npc_id"])
			or _dialogue.history().size() != 1
			or not _history.text.contains(String(npc["display_name"]))
		):
			_fail("NPC reply was not retained in the correct town session")
			return
		await _wait_for_relationship_snapshot()
		if not _relationship.has_verified_snapshot:
			_fail("relationship snapshot was not refreshed for %s" % npc["display_name"])
			return
		_town.close_dialogue_for_testing()

	if not _town.open_dialogue_for_testing(&"neon_guide"):
		_fail("Nia session could not be reopened")
		return
	if (
		_dialogue.conversation_id_for("neon_guide") != _dialogue.conversation_id()
		or _dialogue.history().size() != 1
	):
		_fail("Nia conversation and history were not restored")
		return
	print("GODOT_TOWN_FAKE=PASS npcs=Nia,Ivo,Rhea sessions=3")
	_town.queue_free()
	await process_frame
	quit(0)


func _wait_for_dialogue_state(expected: StringName) -> bool:
	var deadline := Time.get_ticks_msec() + DEADLINE_MILLISECONDS
	while _dialogue.state in [&"loading", &"retrying"] and Time.get_ticks_msec() < deadline:
		await process_frame
	if _dialogue.state != expected:
		_fail("dialogue ended in state %s; status=%s" % [_dialogue.state, _status.text])
		return false
	return true


func _wait_for_relationship_snapshot() -> void:
	var deadline := Time.get_ticks_msec() + 3000
	while not _relationship.has_verified_snapshot and Time.get_ticks_msec() < deadline:
		await process_frame


func _fail(reason: String) -> void:
	printerr("GODOT_TOWN_FAKE=FAIL reason=%s" % reason)
	quit(1)


func _base_url_argument() -> String:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--base-url="):
			return argument.trim_prefix("--base-url=").trim_suffix("/")
	return "http://127.0.0.1:8000"
