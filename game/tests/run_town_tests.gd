extends SceneTree

const TOWN_SCENE_PATH := "res://scenes/town.tscn"
const EXPECTED_IDS := [&"neon_guide", &"signal_archivist", &"night_courier"]
const EXPECTED_LANDMARK_IDS := [
	&"twilight_guide_board",
	&"signal_calibration_station",
	&"rain_delivery_board",
]

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
		"World/LandmarkTwilightGuideBoard",
		"World/LandmarkSignalCalibrationStation",
		"World/LandmarkRainDeliveryBoard",
		"Ui/TownUi/HealthStatus",
		"Ui/TownUi/InteractionPrompt",
		"Ui/TownUi/DialoguePanel",
		"Ui/TownUi/TopicMemoryPopup",
		"Ui/TownUi/ObservationCard",
	]:
		_assert_true(town.has_node(path), "town node exists: %s" % path)
	_assert_equal(town.approved_npc_ids(), EXPECTED_IDS, "three approved NPC ids remain isolated")
	_assert_equal(
		town.approved_landmark_ids(),
		EXPECTED_LANDMARK_IDS,
		"three approved landmark ids remain frozen",
	)
	var expected_topics := {
		&"neon_guide": ["今晚的霓虹夜市有什么值得看的？", "霓虹夜市"],
		&"signal_archivist": ["信号档案里有什么小镇故事？", "小镇故事"],
		&"night_courier": ["雨夜街道会影响投递吗？", "雨夜街道"],
	}
	for npc_id: StringName in expected_topics:
		var profile := town.topic_profile_for_testing(npc_id)
		_assert_equal(profile["draft"], expected_topics[npc_id][0], "fixed topic draft: %s" % npc_id)
		_assert_equal(profile["topic"], expected_topics[npc_id][1], "fixed memory topic: %s" % npc_id)
	var expected_landmarks := {
		&"twilight_guide_board": [
			&"neon_guide",
			"暮光导览牌",
			"我在暮光导览牌上看到傍晚夜市灯带的标记，你会怎么带我逛？",
		],
		&"signal_calibration_station": [
			&"signal_archivist",
			"信号校准台",
			"我在信号校准台看到一段重复的旧广播编号，你知道它的来历吗？",
		],
		&"rain_delivery_board": [
			&"night_courier",
			"雨棚投递板",
			"我在雨棚投递板看到一条褪色的雨夜路线标记，它现在还在使用吗？",
		],
	}
	for landmark_id: StringName in expected_landmarks:
		var profile := town.landmark_profile_for_testing(landmark_id)
		_assert_equal(profile["npc_id"], expected_landmarks[landmark_id][0], "landmark NPC mapping")
		_assert_equal(profile["display_name"], expected_landmarks[landmark_id][1], "landmark name")
		_assert_equal(
			profile["discussion_draft"],
			expected_landmarks[landmark_id][2],
			"landmark discussion draft",
		)

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
	var landmark_target := town.nearest_interaction_target(Vector2(142, 268), 60.0)
	_assert_equal(landmark_target.get("kind"), &"landmark", "landmark can be nearest target")
	_assert_equal(
		landmark_target.get("id"),
		&"twilight_guide_board",
		"nearest landmark uses stable id",
	)
	var tie_target := town.nearest_interaction_target(Vector2(180.5, 268), 60.0)
	_assert_equal(tie_target.get("kind"), &"npc", "NPC wins exact-distance target tie")
	_assert_equal(tie_target.get("id"), &"neon_guide", "tie selects Nia deterministically")
	_assert_true(
		town.nearest_interaction_target(Vector2(20, 500), 40.0).is_empty(),
		"no interaction target outside range",
	)
	_assert_false(
		town.open_observation_for_testing(&"unknown_landmark"),
		"unknown landmark fails closed",
	)
	_assert_true(
		town.open_observation_for_testing(&"twilight_guide_board"),
		"approved landmark opens observation",
	)
	_assert_true(town.is_observation_open(), "observation state opens")
	_assert_true(player.movement_locked, "observation locks player movement")
	_assert_false(
		town.open_dialogue_for_testing(&"neon_guide"),
		"dialogue cannot open over observation",
	)
	town.close_observation_for_testing()
	_assert_false(
		town.has_discovered_landmark(&"twilight_guide_board"),
		"closing observation does not record discovery",
	)
	_assert_false(player.movement_locked, "closing observation restores movement")
	_assert_true(
		town.open_observation_for_testing(&"twilight_guide_board"),
		"landmark observation reopens",
	)
	town.remember_observation_for_testing()
	town.remember_observation_for_testing()
	_assert_true(
		town.has_discovered_landmark(&"twilight_guide_board"),
		"remembering observation is idempotent",
	)
	_assert_true(town.has_discovery_for_npc(&"neon_guide"), "discovery maps to Nia")
	_assert_false(town.has_discovery_for_npc(&"signal_archivist"), "discovery does not leak to Ivo")
	town.close_observation_for_testing()
	_assert_false(town.open_dialogue_for_testing(&"unknown_npc"), "unknown NPC fails closed")
	_assert_true(town.open_dialogue_for_testing(&"neon_guide"), "approved NPC opens dialogue")
	_assert_true(town.is_dialogue_open(), "dialogue state opens")
	_assert_true(player.movement_locked, "dialogue locks player movement")
	var topic_button := town.find_child("TopicMemoryButton", true, false) as Button
	var topic_popup := town.find_child("TopicMemoryPopup", true, false) as PanelContainer
	_assert_true(topic_button != null and topic_popup != null, "topic and memory menu controls exist")
	if topic_button != null and topic_popup != null:
		topic_button.pressed.emit()
		_assert_true(topic_popup.visible, "topic and memory menu opens")
		var topic_title := town.find_child("TopicMemoryTitle", true, false) as Label
		_assert_true(topic_title != null and topic_title.text.contains("Nia"), "menu identifies active NPC")
		var discovery_action := town.find_child("TopicAction6", true, false) as Button
		_assert_true(
			discovery_action != null and discovery_action.visible,
			"Nia menu exposes recorded street discovery",
		)
	town.close_dialogue_for_testing()
	_assert_false(town.is_dialogue_open(), "dialogue state closes")
	_assert_false(player.movement_locked, "closing dialogue restores movement")
	_assert_true(town.open_dialogue_for_testing(&"signal_archivist"), "Ivo opens for isolation check")
	topic_button.pressed.emit()
	var ivo_discovery_action := town.find_child("TopicAction6", true, false) as Button
	_assert_true(
		ivo_discovery_action != null and not ivo_discovery_action.visible,
		"Nia discovery stays hidden from Ivo menu",
	)
	town.close_dialogue_for_testing()
	await _test_dialogue_loop(town, player)
	town.queue_free()
	await process_frame
	await process_frame
	var restarted_town := packed.instantiate() as TownScene
	root.add_child(restarted_town)
	await process_frame
	await process_frame
	for landmark_id: StringName in EXPECTED_LANDMARK_IDS:
		_assert_false(
			restarted_town.has_discovered_landmark(landmark_id),
			"fresh game scene clears startup-only discovery: %s" % landmark_id,
		)
	restarted_town.queue_free()
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
	var topic_button := town.find_child("TopicMemoryButton", true, false) as Button
	var discovery_action := town.find_child("TopicAction6", true, false) as Button
	_assert_true(topic_button != null and discovery_action != null, "context draft controls are present")
	if topic_button == null or discovery_action == null:
		return
	topic_button.pressed.emit()
	_assert_true(discovery_action.visible, "recorded Nia discovery remains available")
	discovery_action.pressed.emit()
	var frozen_draft := "我在暮光导览牌上看到傍晚夜市灯带的标记，你会怎么带我逛？"
	_assert_equal(input.text, frozen_draft, "discovery action fills visible draft without sending")
	_assert_equal(bodies.size(), 0, "filling context draft performs no network request")
	input.text += " 我还想知道路线。"
	input.text_changed.emit(input.text)
	_assert_false(send.disabled, "Send enables for valid input")
	send.pressed.emit()
	_assert_equal(dialogue.state, &"loading", "town renders loading request")
	town.close_dialogue_for_testing()
	_assert_true(town.is_dialogue_open(), "dialogue cannot close while request is pending")
	_assert_false(town.open_dialogue_for_testing(&"signal_archivist"), "NPC cannot switch in flight")
	_assert_true(player.movement_locked, "player stays locked during request")

	var first_payload: Dictionary = JSON.parse_string(bodies[0])
	_assert_equal(
		first_payload["message"],
		frozen_draft + " 我还想知道路线。",
		"edited visible context is the exact network message",
	)
	var success := _dialogue_success(first_payload, "Nia 指出了夜市灯带的路线。", "completed")
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		JSON.stringify(success).to_utf8_buffer(),
	)
	_assert_equal(dialogue.history().size(), 1, "successful turn enters Nia history")
	_assert_true(history.text.contains("我还想知道路线"), "visible history contains edited player text")
	_assert_true(history.text.contains("夜市灯带的路线"), "visible history contains NPC reply")
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
	relationship._set_state(&"unavailable")
	_assert_equal(relationship_label.text, "关系 · 暂不可用", "failed refresh hides stale stage")
	town.close_dialogue_for_testing()
	_test_guided_memory_action(town, dialogue, bodies)


func _test_guided_memory_action(town: TownScene, dialogue: Node, bodies: Array[String]) -> void:
	_assert_true(town.open_dialogue_for_testing(&"night_courier"), "Rhea opens for guided memory")
	var topic_button := town.find_child("TopicMemoryButton", true, false) as Button
	var remember_button := town.find_child("TopicAction1", true, false) as Button
	var confirm_button := town.find_child("TopicMemoryConfirmButton", true, false) as Button
	var cancel_button := town.find_child("TopicMemoryCancelButton", true, false) as Button
	var confirmation := town.find_child("TopicMemoryConfirmationText", true, false) as Label
	var history := town.find_child("ConversationHistory", true, false) as RichTextLabel
	var retry := town.find_child("RetryButton", true, false) as Button
	_assert_true(
		topic_button != null
		and remember_button != null
		and confirm_button != null
		and cancel_button != null,
		"guided memory controls are present",
	)
	if (
		topic_button == null
		or remember_button == null
		or confirm_button == null
		or cancel_button == null
		or confirmation == null
		or history == null
		or retry == null
	):
		return

	var body_count := bodies.size()
	topic_button.pressed.emit()
	remember_button.pressed.emit()
	_assert_true(confirmation.text.contains("Rhea"), "confirmation identifies active NPC")
	_assert_true(confirmation.text.contains("雨夜街道"), "confirmation identifies exact topic")
	_assert_equal(bodies.size(), body_count, "state write does not send before confirmation")
	cancel_button.pressed.emit()
	_assert_equal(bodies.size(), body_count, "cancelled state write stays local")

	remember_button.pressed.emit()
	confirm_button.pressed.emit()
	_assert_equal(dialogue.state, &"loading", "confirmed state write starts one request")
	var first_payload_json := bodies[-1]
	var first_payload: Dictionary = JSON.parse_string(first_payload_json)
	_assert_equal(
		first_payload["message"],
		"请记住：favorite_cyber_town_topic=雨夜街道",
		"guided action preserves deterministic raw payload",
	)
	_assert_true(confirm_button.disabled and cancel_button.disabled, "menu locks during request")
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_TIMEOUT,
		0,
		PackedByteArray(),
	)
	_assert_true(retry.visible and not retry.disabled, "guided action exposes exact retry")
	retry.pressed.emit()
	_assert_equal(bodies[-1], first_payload_json, "guided retry preserves byte-identical payload")
	var success := _dialogue_success(
		first_payload,
		"已记住：favorite_cyber_town_topic。",
		"completed",
	)
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		JSON.stringify(success).to_utf8_buffer(),
	)
	var rhea_history: Array[Dictionary] = dialogue.history()
	_assert_equal(rhea_history.size(), 1, "guided retry appends one history turn")
	_assert_equal(rhea_history[0]["action_kind"], "remember_topic", "history retains action type")
	_assert_true(
		String(rhea_history[0]["message"]).contains("雨夜街道"),
		"history uses friendly display text",
	)
	_assert_false(
		String(rhea_history[0]["message"]).contains("favorite_cyber_town_topic"),
		"history hides internal fact key",
	)
	_assert_true(history.text.contains("系统：Rhea 已记下"), "history renders a system confirmation")
	_assert_false(history.text.contains("favorite_cyber_town_topic"), "rendered history hides fact key")
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
