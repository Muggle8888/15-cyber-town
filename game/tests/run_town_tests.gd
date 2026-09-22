extends SceneTree

const TOWN_SCENE_PATH := "res://scenes/town.tscn"
const EVENT_TEST_SAVE_PATH := "res://.godot/f013-event-state-test.json"
const AFTERMATH_TEST_SAVE_PATH := "res://.godot/f014-aftermath-state-test.json"
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
	ProjectSettings.set_setting("cyber_town/testing/event_save_path", EVENT_TEST_SAVE_PATH)
	ProjectSettings.set_setting(
		"cyber_town/testing/aftermath_save_path",
		AFTERMATH_TEST_SAVE_PATH,
	)
	_test_event_state_persistence()
	_test_aftermath_state_persistence()
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
		"Ui/TownUi/EventTracker",
		"Ui/TownUi/InteractionPrompt",
		"Ui/TownUi/DialoguePanel",
		"Ui/TownUi/TopicMemoryPopup",
		"Ui/TownUi/ObservationCard",
	]:
		_assert_true(town.has_node(path), "town node exists: %s" % path)
	var event_tracker := town.find_child("EventTracker", true, false) as Panel
	var event_body := town.find_child("EventTrackerBody", true, false) as Control
	var event_toggle := town.find_child("EventTrackerToggle", true, false) as Button
	var event_progress := town.find_child("EventProgress", true, false) as Label
	var event_title := town.find_child("EventTitle", true, false) as Label
	var event_objective := town.find_child("EventObjective", true, false) as Label
	_assert_true(
		event_tracker != null and event_body != null and event_toggle != null,
		"event tracker controls exist",
	)
	_assert_true(
		event_progress != null and event_progress.text == "街区事件 · 1/7",
		"event tracker shows frozen progress",
	)
	_assert_true(
		event_title != null and event_title.text == "暮光失联信号",
		"event tracker shows frozen title",
	)
	_assert_true(
		event_objective != null and event_objective.text.contains("Nia"),
		"event tracker shows the current target",
	)
	var initial_event_profile := town.event_profile_for_testing()
	var relationship_drafts: Dictionary = {}
	var completion_lines: Dictionary = {}
	for relationship_stage: String in ["newcomer", "acquaintance", "friend", "trusted_ally"]:
		var relationship_draft: String = town._event_draft_for_stage(
			initial_event_profile,
			relationship_stage,
		)
		_assert_true(
			relationship_draft.contains("夜市灯带"),
			"relationship event draft preserves the authored clue: %s" % relationship_stage,
		)
		relationship_drafts[relationship_draft] = true
		completion_lines[town._event_completion_line_for_stage(relationship_stage)] = true
	_assert_equal(
		relationship_drafts.size(),
		4,
		"four relationship stages produce distinct event drafts",
	)
	_assert_equal(completion_lines.size(), 4, "four relationship stages produce distinct completion lines")
	if event_body != null and event_toggle != null:
		event_toggle.pressed.emit()
		_assert_false(event_body.visible, "event tracker collapses")
		event_toggle.pressed.emit()
		_assert_true(event_body.visible, "event tracker expands")
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
	_assert_equal(
		restarted_town.event_stage_for_testing(),
		&"completed",
		"event completion persists across a fresh town scene",
	)
	_assert_equal(
		restarted_town.aftermath_stage_for_testing(),
		&"completed",
		"aftermath completion persists across a fresh town scene",
	)
	_assert_equal(
		restarted_town.aftermath_outcome_for_testing(),
		&"archive_monitor",
		"selected aftermath outcome persists across a fresh town scene",
	)
	var restarted_visual := restarted_town.aftermath_visual_for_testing()
	_assert_equal(restarted_visual.get("label"), "档案监听", "persisted outcome restores signal sign")
	var replay_toggle := restarted_town.find_child("EventTrackerToggle", true, false) as Button
	var reset_panel := restarted_town.find_child("EventResetConfirmation", true, false) as Panel
	var reset_cancel := restarted_town.find_child("EventResetCancelButton", true, false) as Button
	var reset_confirm := restarted_town.find_child("EventResetConfirmButton", true, false) as Button
	var replay_prelude := restarted_town.find_child("EventReplayPreludeButton", true, false) as Button
	_assert_true(
		replay_toggle != null
		and reset_panel != null
		and reset_cancel != null
		and reset_confirm != null
		and replay_prelude != null,
		"completed aftermath exposes independent replay controls",
	)
	if (
		replay_toggle != null
		and reset_panel != null
		and reset_cancel != null
		and reset_confirm != null
		and replay_prelude != null
	):
		replay_toggle.pressed.emit()
		_assert_true(reset_panel.visible, "aftermath replay opens a second confirmation")
		reset_cancel.pressed.emit()
		_assert_false(reset_panel.visible, "aftermath replay can be cancelled")
		replay_toggle.pressed.emit()
		_assert_true(replay_prelude.visible, "completed aftermath offers prelude replay")
		replay_prelude.pressed.emit()
		_assert_equal(
			restarted_town.event_stage_for_testing(),
			&"nia_intro",
			"prelude replay resets F-013",
		)
		_assert_equal(
			restarted_town.aftermath_stage_for_testing(),
			&"completed",
			"prelude replay preserves F-014 progression",
		)
	restarted_town.queue_free()
	await process_frame
	_finish()


func _test_event_state_persistence() -> void:
	var invalid_file := FileAccess.open(EVENT_TEST_SAVE_PATH, FileAccess.WRITE)
	_assert_true(invalid_file != null, "event test save is writable")
	if invalid_file != null:
		invalid_file.store_string("{invalid-json")
		invalid_file.close()
	var recovered := TwilightSignalEventState.new(EVENT_TEST_SAVE_PATH)
	var warning: String = recovered.load_or_start()
	_assert_true(not warning.is_empty(), "invalid event save produces a non-blocking warning")
	_assert_equal(recovered.stage, &"nia_intro", "invalid event save recovers to the first step")
	_assert_false(
		recovered.advance_dialogue(&"signal_archivist", "completed"),
		"wrong NPC cannot advance an event dialogue step",
	)
	_assert_false(
		recovered.advance_dialogue(&"neon_guide", "degraded"),
		"degraded dialogue cannot advance the event",
	)
	_assert_true(
		recovered.advance_dialogue(&"neon_guide", "completed"),
		"matching completed dialogue advances the event",
	)
	_assert_false(
		recovered.record_landmark(&"signal_calibration_station"),
		"future landmark cannot skip the current clue",
	)
	_assert_true(
		recovered.record_landmark(&"twilight_guide_board"),
		"matching landmark records and advances the event",
	)
	var restored := TwilightSignalEventState.new(EVENT_TEST_SAVE_PATH)
	_assert_equal(restored.load_or_start(), "", "valid event save reloads without warning")
	_assert_equal(restored.stage, &"ivo_analysis", "event stage survives controller recreation")
	_assert_true(
		&"twilight_guide_board" in restored.recorded_clues,
		"recorded event clue survives controller recreation",
	)
	_assert_true(restored.reset_event(), "event state can be reset deterministically")


func _test_aftermath_state_persistence() -> void:
	var invalid_file := FileAccess.open(AFTERMATH_TEST_SAVE_PATH, FileAccess.WRITE)
	_assert_true(invalid_file != null, "aftermath test save is writable")
	if invalid_file != null:
		invalid_file.store_string("{invalid-json")
		invalid_file.close()
	var recovered := TwilightSignalAftermathState.new(AFTERMATH_TEST_SAVE_PATH)
	var warning: String = recovered.load_or_initialize(false)
	_assert_true(not warning.is_empty(), "invalid aftermath save produces a non-blocking warning")
	_assert_equal(recovered.stage, &"locked", "aftermath remains locked before F-013 completion")
	_assert_false(recovered.unlock_if_ready(false), "unfinished prerequisite cannot unlock aftermath")
	_assert_true(recovered.unlock_if_ready(true), "completed prerequisite unlocks aftermath once")
	_assert_false(recovered.unlock_if_ready(true), "aftermath unlock is idempotent")
	_assert_false(
		recovered.record_dialogue(&"signal_archivist", &"consultation", "completed"),
		"Ivo cannot replace the required Nia briefing",
	)
	_assert_false(
		recovered.record_dialogue(&"neon_guide", &"consultation", "degraded"),
		"degraded briefing cannot advance aftermath",
	)
	_assert_true(
		recovered.record_dialogue(&"neon_guide", &"consultation", "completed"),
		"Nia briefing starts consultation",
	)
	_assert_true(
		recovered.record_dialogue(&"night_courier", &"consultation", "completed"),
		"Rhea consultation can precede Ivo",
	)
	_assert_false(
		recovered.choose_outcome(&"archive_monitor"),
		"outcome stays locked until all three opinions are recorded",
	)
	_assert_false(
		recovered.record_dialogue(&"night_courier", &"consultation", "completed"),
		"duplicate consultation does not count twice",
	)
	_assert_true(
		recovered.record_dialogue(&"signal_archivist", &"consultation", "completed"),
		"Ivo consultation makes the decision available",
	)
	_assert_equal(recovered.stage, &"decision_ready", "three opinions unlock deterministic choice")
	_assert_true(recovered.choose_outcome(&"archive_monitor"), "approved outcome can be selected")
	_assert_equal(recovered.outcome_display_name(), "档案监听", "selected outcome has authored label")
	_assert_false(
		recovered.record_dialogue(&"neon_guide", &"consultation", "completed"),
		"old consultation response cannot advance the reaction phase",
	)
	_assert_true(
		recovered.record_dialogue(&"night_courier", &"reaction", "completed"),
		"Rhea reaction can be recorded first",
	)
	_assert_true(
		recovered.record_dialogue(&"neon_guide", &"reaction", "completed"),
		"Nia reaction can be recorded second",
	)
	_assert_true(
		recovered.record_dialogue(&"signal_archivist", &"reaction", "completed"),
		"Ivo reaction completes aftermath",
	)
	_assert_true(recovered.is_completed(), "three independent reactions complete aftermath")
	var restored := TwilightSignalAftermathState.new(AFTERMATH_TEST_SAVE_PATH)
	_assert_equal(restored.load_or_initialize(true), "", "valid aftermath save reloads cleanly")
	_assert_equal(restored.stage, &"completed", "aftermath stage survives controller recreation")
	_assert_equal(restored.selected_outcome, &"archive_monitor", "outcome survives controller recreation")
	_assert_true(
		&"night_courier" in restored.reacted_npcs,
		"reaction set survives controller recreation",
	)
	_assert_true(restored.reset_event(true), "aftermath reset succeeds independently")
	_assert_equal(restored.stage, &"nia_briefing", "aftermath reset preserves completed prerequisite")
	_assert_true(restored.selected_outcome.is_empty(), "aftermath reset clears only its outcome")
	_assert_true(restored.reset_event(false), "aftermath can return to locked state for test isolation")

	var expected_outcomes := {
		&"night_market_guide": "夜市导引",
		&"archive_monitor": "档案监听",
		&"rain_route_beacon": "雨夜信标",
	}
	for outcome_id: StringName in expected_outcomes:
		var state := TwilightSignalAftermathState.new()
		state.load_or_initialize(true)
		state.record_dialogue(&"neon_guide", &"consultation", "completed")
		state.record_dialogue(&"signal_archivist", &"consultation", "completed")
		state.record_dialogue(&"night_courier", &"consultation", "completed")
		_assert_true(state.choose_outcome(outcome_id), "outcome is reachable: %s" % outcome_id)
		_assert_equal(
			state.outcome_display_name(),
			expected_outcomes[outcome_id],
			"outcome owns the expected player-visible label",
		)


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
	_test_twilight_signal_event(town, dialogue, bodies)
	_test_twilight_signal_aftermath(town, dialogue, bodies)


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


func _test_twilight_signal_event(town: TownScene, dialogue: Node, bodies: Array[String]) -> void:
	_assert_equal(town.event_stage_for_testing(), &"nia_intro", "event starts at the Nia step")
	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"nia_intro", "degraded")
	_assert_equal(town.event_stage_for_testing(), &"nia_intro", "degraded event reply does not advance")
	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"nia_intro", "completed")
	_assert_equal(town.event_stage_for_testing(), &"guide_clue", "Nia completion unlocks guide clue")

	_assert_true(
		town.open_observation_for_testing(&"signal_calibration_station"),
		"future landmark remains available as a normal observation",
	)
	town.remember_observation_for_testing()
	_assert_equal(town.event_stage_for_testing(), &"guide_clue", "future landmark cannot skip event stage")
	town.close_observation_for_testing()
	_assert_true(
		town.open_observation_for_testing(&"twilight_guide_board"),
		"current guide landmark opens",
	)
	var event_clue_button := town.find_child("ObservationRememberButton", true, false) as Button
	_assert_true(
		event_clue_button != null and event_clue_button.text == "记录事件线索",
		"current landmark exposes the explicit event action",
	)
	town.remember_observation_for_testing()
	_assert_equal(town.event_stage_for_testing(), &"ivo_analysis", "guide clue advances to Ivo")
	town.close_observation_for_testing()

	_complete_event_dialogue(town, dialogue, bodies, &"signal_archivist", &"ivo_analysis", "timeout")
	_assert_equal(town.event_stage_for_testing(), &"signal_clue", "retried Ivo reply advances event")
	_assert_true(
		town.open_observation_for_testing(&"signal_calibration_station"),
		"current signal landmark opens",
	)
	town.remember_observation_for_testing()
	_assert_equal(town.event_stage_for_testing(), &"rhea_route", "signal clue advances to Rhea")
	town.close_observation_for_testing()

	_complete_event_dialogue(town, dialogue, bodies, &"night_courier", &"rhea_route", "completed")
	_assert_equal(town.event_stage_for_testing(), &"delivery_clue", "Rhea unlocks delivery clue")
	_assert_true(
		town.open_observation_for_testing(&"rain_delivery_board"),
		"current delivery landmark opens",
	)
	town.remember_observation_for_testing()
	_assert_equal(town.event_stage_for_testing(), &"nia_conclusion", "delivery clue returns to Nia")
	town.close_observation_for_testing()

	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"nia_conclusion", "completed")
	_assert_equal(town.event_stage_for_testing(), &"completed", "final Nia reply completes the event")
	_assert_equal(
		town.aftermath_stage_for_testing(),
		&"nia_briefing",
		"F-013 completion unlocks F-014 exactly once",
	)
	var event_progress := town.find_child("EventProgress", true, false) as Label
	var event_title := town.find_child("EventTitle", true, false) as Label
	var event_objective := town.find_child("EventObjective", true, false) as Label
	_assert_true(
		event_progress != null and event_progress.text == "街区事件 · 1/7",
		"completed prelude transitions to aftermath progress",
	)
	_assert_true(
		event_title != null and event_title.text == "暮光信号余波",
		"completed prelude transitions to the aftermath tracker",
	)
	_assert_true(
		event_objective != null and event_objective.text.contains("Nia"),
		"aftermath tracker points to Nia briefing",
	)


func _test_twilight_signal_aftermath(
	town: TownScene,
	dialogue: Node,
	bodies: Array[String],
) -> void:
	_assert_equal(town.aftermath_stage_for_testing(), &"nia_briefing", "aftermath starts at Nia")
	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"nia_briefing", "degraded")
	_assert_equal(town.aftermath_stage_for_testing(), &"nia_briefing", "degraded briefing does not advance")
	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"nia_briefing", "completed")
	_assert_equal(town.aftermath_stage_for_testing(), &"consulting", "Nia briefing opens consultation")

	_complete_event_dialogue(town, dialogue, bodies, &"night_courier", &"consulting", "completed")
	_assert_equal(town.aftermath_stage_for_testing(), &"consulting", "Rhea can be consulted before Ivo")
	_complete_event_dialogue(town, dialogue, bodies, &"signal_archivist", &"consulting", "timeout")
	_assert_equal(
		town.aftermath_stage_for_testing(),
		&"decision_ready",
		"three opinions unlock the deterministic decision",
	)

	var body_count := bodies.size()
	_assert_true(town._open_aftermath_choice(), "decision-ready signal station opens choice panel")
	var choice_panel := town.find_child("AftermathChoicePanel", true, false) as Panel
	var archive_choice := town.find_child("AftermathChoice1", true, false) as Button
	var choice_confirmation := town.find_child("AftermathChoiceConfirmation", true, false) as Panel
	var choice_confirm := town.find_child("AftermathChoiceConfirm", true, false) as Button
	_assert_true(
		choice_panel != null
		and archive_choice != null
		and choice_confirmation != null
		and choice_confirm != null,
		"aftermath choice and confirmation controls exist",
	)
	if (
		choice_panel != null
		and archive_choice != null
		and choice_confirmation != null
		and choice_confirm != null
	):
		_assert_true(choice_panel.visible, "choice panel is visible at the signal station")
		archive_choice.pressed.emit()
		_assert_true(choice_confirmation.visible, "outcome requires a second confirmation")
		_assert_equal(bodies.size(), body_count, "opening and selecting an outcome performs no request")
		choice_confirm.pressed.emit()
		_assert_equal(bodies.size(), body_count, "confirming an outcome performs no Provider request")
	_assert_equal(town.aftermath_stage_for_testing(), &"aftermath", "confirmed choice starts reactions")
	_assert_equal(town.aftermath_outcome_for_testing(), &"archive_monitor", "choice is saved deterministically")
	var visual := town.aftermath_visual_for_testing()
	_assert_equal(visual.get("label"), "档案监听", "selected outcome updates the station sign")
	_assert_true(
		String(visual.get("accent", "")).begins_with("9a8cff"),
		"selected outcome applies the archive accent",
	)

	_complete_event_dialogue(town, dialogue, bodies, &"signal_archivist", &"aftermath", "completed")
	_assert_equal(town.aftermath_stage_for_testing(), &"aftermath", "one reaction does not complete aftermath")
	_complete_event_dialogue(town, dialogue, bodies, &"neon_guide", &"aftermath", "completed")
	_assert_equal(town.aftermath_stage_for_testing(), &"aftermath", "two reactions do not complete aftermath")
	_complete_event_dialogue(town, dialogue, bodies, &"night_courier", &"aftermath", "completed")
	_assert_equal(town.aftermath_stage_for_testing(), &"completed", "three reactions complete aftermath")
	var event_progress := town.find_child("EventProgress", true, false) as Label
	var event_objective := town.find_child("EventObjective", true, false) as Label
	_assert_true(
		event_progress != null and event_progress.text == "街区事件 · 7/7",
		"completed aftermath renders final progress",
	)
	_assert_true(
		event_objective != null and event_objective.text.contains("档案监听"),
		"completed aftermath renders the selected outcome summary",
	)


func _complete_event_dialogue(
	town: TownScene,
	dialogue: Node,
	bodies: Array[String],
	npc_id: StringName,
	expected_stage: StringName,
	mode: String,
) -> void:
	var active_stage := (
		town.aftermath_stage_for_testing()
		if town.event_stage_for_testing() == &"completed"
		else town.event_stage_for_testing()
	)
	_assert_equal(active_stage, expected_stage, "event helper starts at expected stage")
	_assert_true(town.open_dialogue_for_testing(npc_id), "event target NPC opens: %s" % npc_id)
	var topic_button := town.find_child("TopicMemoryButton", true, false) as Button
	var event_button := town.find_child("TopicAction7", true, false) as Button
	var input := town.find_child("MessageInput", true, false) as LineEdit
	var send := town.find_child("SendButton", true, false) as Button
	var retry := town.find_child("RetryButton", true, false) as Button
	var status := town.find_child("DialogueStatus", true, false) as Label
	_assert_true(
		topic_button != null and event_button != null and input != null and send != null,
		"event dialogue controls are present",
	)
	if (
		topic_button == null
		or event_button == null
		or input == null
		or send == null
		or retry == null
		or status == null
	):
		return
	var body_count := bodies.size()
	topic_button.pressed.emit()
	_assert_true(event_button.visible, "event action is visible only for the current NPC")
	event_button.pressed.emit()
	_assert_equal(bodies.size(), body_count, "event action fills a draft without sending")
	_assert_true(not input.text.is_empty(), "event action fills visible text")
	input.text += " 我想确认这条线索。"
	input.text_changed.emit(input.text)
	var visible_message := input.text
	send.pressed.emit()
	var payload_json := bodies[-1]
	var payload: Dictionary = JSON.parse_string(payload_json)
	_assert_equal(payload.size(), 5, "event request keeps the public Dialogue v1 schema")
	_assert_false(payload.has("event_id"), "event step is never sent as hidden API context")
	_assert_equal(payload["npc_id"], String(npc_id), "event payload uses the current NPC")
	_assert_equal(payload["message"], visible_message, "event payload equals edited visible text")
	if mode == "timeout":
		dialogue.handle_response(
			dialogue.active_generation(),
			HTTPRequest.RESULT_TIMEOUT,
			0,
			PackedByteArray(),
		)
		_assert_true(retry.visible and not retry.disabled, "event timeout exposes manual retry")
		retry.pressed.emit()
		_assert_equal(bodies[-1], payload_json, "event retry reuses the byte-identical payload")
		mode = "completed"
	var response := _dialogue_success(payload, "合成事件回复。", mode)
	dialogue.handle_response(
		dialogue.active_generation(),
		HTTPRequest.RESULT_SUCCESS,
		200,
		JSON.stringify(response).to_utf8_buffer(),
	)
	if mode == "degraded":
		_assert_true(status.text.contains("事件尚未推进"), "degraded event reply explains no progress")
	else:
		_assert_true(status.text.contains("事件已推进"), "completed event reply explains progress")
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
