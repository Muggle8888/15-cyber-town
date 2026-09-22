extends SceneTree

const TOWN_SCENE_PATH := "res://scenes/town.tscn"
const EXPECTED_IDS := [&"neon_guide", &"signal_archivist", &"night_courier"]

var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	_assert_equal(
		ProjectSettings.get_setting("application/run/main_scene"),
		TOWN_SCENE_PATH,
		"town is the product main scene",
	)
	var packed := load(TOWN_SCENE_PATH) as PackedScene
	_assert_true(packed != null, "town scene loads")
	if packed == null:
		_finish()
		return
	var town := packed.instantiate() as TownScene
	root.add_child(town)
	await process_frame
	await process_frame

	for path: String in [
		"Ground/Grass",
		"World/Player/Camera2D",
		"World/Nia",
		"World/Ivo",
		"World/Rhea",
		"Ui/TownUi/HealthStatus",
		"Ui/TownUi/InteractionPrompt",
		"Ui/TownUi/DialoguePanel",
	]:
		_assert_true(town.has_node(path), "town node exists: %s" % path)
	_assert_equal(town.approved_npc_ids(), EXPECTED_IDS, "three approved NPC ids remain isolated")

	var player := town.player()
	_assert_true(player != null, "player exists")
	if player != null:
		_assert_equal(player.move_speed, 92.0, "player speed is frozen")
		var diagonal := player.normalized_velocity_for_input(Vector2(1.0, 1.0))
		_assert_true(is_equal_approx(diagonal.length(), 92.0), "diagonal speed is normalized")
		var camera := player.get_node("Camera2D") as Camera2D
		_assert_false(camera.position_smoothing_enabled, "camera smoothing is disabled")
		_assert_equal(camera.limit_left, 0, "camera left boundary")
		_assert_equal(camera.limit_top, 0, "camera top boundary")
		_assert_equal(camera.limit_right, 960, "camera right boundary")
		_assert_equal(camera.limit_bottom, 540, "camera bottom boundary")

	var nearest := town.nearest_npc(Vector2(219, 268), 60.0)
	_assert_true(nearest != null, "nearest NPC is found inside range")
	if nearest != null:
		_assert_equal(nearest.npc_id, "neon_guide", "nearest target selects Nia")
	_assert_true(town.nearest_npc(Vector2(20, 500), 40.0) == null, "no target outside range")
	_assert_false(town.open_dialogue_for_testing(&"unknown_npc"), "unknown NPC fails closed")
	_assert_true(town.open_dialogue_for_testing(&"neon_guide"), "approved NPC opens dialogue")
	_assert_true(town.is_dialogue_open(), "dialogue state opens")
	_assert_true(player.movement_locked, "dialogue locks player movement")
	town.close_dialogue_for_testing()
	_assert_false(town.is_dialogue_open(), "dialogue state closes")
	_assert_false(player.movement_locked, "closing dialogue restores movement")
	await _test_dialogue_loop(town, player)
	town.queue_free()
	await process_frame
	await process_frame
	_finish()


func _test_dialogue_loop(town: TownScene, player: TownPlayerController) -> void:
	var dialogue: Node = town.dialogue_client_for_testing()
	var relationship: Node = town.relationship_client_for_testing()
	var bodies: Array[String] = []
	dialogue.set_request_sender_for_testing(func(
		_url: String,
		_headers: PackedStringArray,
		_method: int,
		body: String,
	) -> int:
		bodies.append(body)
		return OK
	)
	relationship.set_request_sender_for_testing(func(
		_url: String,
		_headers: PackedStringArray,
	) -> int:
		return OK
	)
	town.set_backend_available_for_testing(true)

	_assert_true(town.open_dialogue_for_testing(&"neon_guide"), "Nia dialogue reopens")
	var nia_conversation: String = dialogue.conversation_id()
	var input := town.find_child("MessageInput", true, false) as LineEdit
	var send := town.find_child("SendButton", true, false) as Button
	var retry := town.find_child("RetryButton", true, false) as Button
	var status := town.find_child("DialogueStatus", true, false) as Label
	var history := town.find_child("ConversationHistory", true, false) as RichTextLabel
	_assert_true(input != null and send != null and retry != null, "dialogue controls are present")
	if input == null or send == null or retry == null or status == null or history == null:
		return
	input.text = "记住广场的灯"
	input.text_changed.emit(input.text)
	_assert_false(send.disabled, "Send enables for valid input")
	send.pressed.emit()
	_assert_equal(dialogue.state, &"loading", "town renders loading request")
	town.close_dialogue_for_testing()
	_assert_true(town.is_dialogue_open(), "dialogue cannot close while request is pending")
	_assert_false(town.open_dialogue_for_testing(&"signal_archivist"), "NPC cannot switch in flight")
	_assert_true(player.movement_locked, "player stays locked during request")

	var first_payload: Dictionary = JSON.parse_string(bodies[0])
	var success := _dialogue_success(first_payload, "Nia 记住了广场的灯。", "completed")
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		JSON.stringify(success).to_utf8_buffer(),
	)
	_assert_equal(dialogue.history().size(), 1, "successful turn enters Nia history")
	_assert_true(history.text.contains("记住广场的灯"), "visible history contains player text")
	_assert_true(history.text.contains("Nia 记住了"), "visible history contains NPC reply")
	town.close_dialogue_for_testing()
	_assert_true(town.open_dialogue_for_testing(&"signal_archivist"), "Ivo opens after completion")
	var ivo_conversation: String = dialogue.conversation_id()
	_assert_true(ivo_conversation != nia_conversation, "Ivo owns a distinct conversation")
	_assert_equal(dialogue.history().size(), 0, "Ivo does not inherit Nia history")
	town.close_dialogue_for_testing()
	_assert_true(town.open_dialogue_for_testing(&"neon_guide"), "Nia opens again")
	_assert_equal(dialogue.conversation_id(), nia_conversation, "Nia conversation resumes")
	_assert_equal(dialogue.history().size(), 1, "Nia history resumes")

	input.text = "再说一次"
	input.text_changed.emit(input.text)
	send.pressed.emit()
	var retry_payload: String = bodies[-1]
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_TIMEOUT,
		0,
		PackedByteArray(),
	)
	_assert_true(retry.visible and not retry.disabled, "timeout exposes manual retry")
	retry.pressed.emit()
	_assert_equal(bodies[-1], retry_payload, "retry reuses the exact frozen payload")
	var second_payload: Dictionary = JSON.parse_string(bodies[-1])
	var degraded := _dialogue_success(second_payload, "线路不稳，但我还在。", "degraded")
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		JSON.stringify(degraded).to_utf8_buffer(),
	)
	_assert_equal(dialogue.history().size(), 2, "retry adds one visible turn without duplication")
	_assert_true(status.text.contains("临时回应"), "degraded response is explained to the player")
	_assert_true(history.text.contains("（临时回应）"), "degraded turn is marked in history")

	var relation_payload := {
		"npc_id": "neon_guide",
		"score": 21,
		"stage": "friend",
		"rule_version": "f-006-v1",
		"event": {
			"category": "friendly",
			"applied_delta": 1,
			"reason_code": "rule_friendly",
			"score": 21,
			"stage": "friend",
			"occurred_at": 1,
		},
	}
	relationship.handle_response(
		relationship.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		PackedStringArray(["Content-Type: application/json"]),
		JSON.stringify(relation_payload).to_utf8_buffer(),
	)
	var relationship_label := town._relationship_label as Label
	_assert_true(relationship_label.text.contains("朋友"), "relationship stage is localized")
	_assert_true(relationship_label.text.contains("关系升温"), "relationship delta is summarized")
	town.close_dialogue_for_testing()


func _dialogue_success(request: Dictionary, reply: String, response_status: String) -> Dictionary:
	return {
		"request_id": request["request_id"],
		"trace_id": "33333333-3333-4333-8333-333333333333",
		"npc_id": request["npc_id"],
		"conversation_id": request["conversation_id"],
		"reply": reply,
		"status": response_status,
		"provider": "synthetic",
	}


func _finish() -> void:
	if _failures.is_empty():
		print("TOWN_TESTS=PASS")
		quit(0)
		return
	for failure: String in _failures:
		printerr("TOWN_TEST_FAILURE: %s" % failure)
	printerr("TOWN_TESTS=FAIL count=%d" % _failures.size())
	quit(1)


func _assert_true(value: bool, label: String) -> void:
	if not value:
		_failures.append(label)


func _assert_false(value: bool, label: String) -> void:
	_assert_true(not value, label)


func _assert_equal(actual: Variant, expected: Variant, label: String) -> void:
	if actual != expected:
		_failures.append("%s (expected=%s, actual=%s)" % [label, expected, actual])
