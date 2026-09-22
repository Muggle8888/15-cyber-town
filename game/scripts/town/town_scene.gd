class_name TownScene
extends Node2D

const WORLD_SIZE := Vector2(960.0, 540.0)
const INTERACTION_DISTANCE := 58.0
const APPROVED_NPC_IDS := [&"neon_guide", &"signal_archivist", &"night_courier"]
const GRASS_TEXTURE := preload("res://assets/third_party/tiny_rpg_fantasy/tiny-rpg-town-files/Assets/Environments/Town/tileset/grass-tile-2.png")
const TILESET_TEXTURE := preload("res://assets/third_party/tiny_rpg_fantasy/tiny-rpg-town-files/Assets/Environments/Town/tileset/tileset.png")
const PLAYER_SCENE := preload("res://scenes/player.tscn")
const NPC_SCENE := preload("res://scenes/npc_actor.tscn")
const HEALTH_CLIENT_SCRIPT := preload("res://scripts/backend_health_client.gd")
const DIALOGUE_CLIENT_SCRIPT := preload("res://scripts/dialogue/dialogue_client.gd")
const RELATIONSHIP_CLIENT_SCRIPT := preload("res://scripts/dialogue/relationship_client.gd")
const UI_FONT := preload("res://assets/third_party/noto_sans_cjk_sc_complete/NotoSansCJKsc-Regular.otf")
const INTERACTION_SOUND := preload("res://assets/third_party/kenney_rpg_audio/Audio/bookOpen.ogg")
const BUTTON_SOUND := preload("res://assets/third_party/kenney_rpg_audio/Audio/metalClick.ogg")
const NPC_TOPIC_PROFILES := {
	&"neon_guide": {
		"display_name": "Nia",
		"topic": "霓虹夜市",
		"draft": "今晚的霓虹夜市有什么值得看的？",
	},
	&"signal_archivist": {
		"display_name": "Ivo",
		"topic": "小镇故事",
		"draft": "信号档案里有什么小镇故事？",
	},
	&"night_courier": {
		"display_name": "Rhea",
		"topic": "雨夜街道",
		"draft": "雨夜街道会影响投递吗？",
	},
}
const LANDMARK_PROFILES := {
	&"twilight_guide_board": {
		"display_name": "暮光导览牌",
		"short_label": "导览牌",
		"observation": "导览牌标出一条只在傍晚亮起的夜市灯带。",
		"npc_id": &"neon_guide",
		"npc_name": "Nia",
		"discussion_draft": "我在暮光导览牌上看到傍晚夜市灯带的标记，你会怎么带我逛？",
		"position": Vector2(142, 268),
		"accent": "#70d6c8",
	},
	&"signal_calibration_station": {
		"display_name": "信号校准台",
		"short_label": "校准台",
		"observation": "校准记录中反复出现同一段旧广播编号。",
		"npc_id": &"signal_archivist",
		"npc_name": "Ivo",
		"discussion_draft": "我在信号校准台看到一段重复的旧广播编号，你知道它的来历吗？",
		"position": Vector2(620, 244),
		"accent": "#73b9d8",
	},
	&"rain_delivery_board": {
		"display_name": "雨棚投递板",
		"short_label": "投递板",
		"observation": "投递板上留有一条褪色的雨夜路线标记。",
		"npc_id": &"night_courier",
		"npc_name": "Rhea",
		"discussion_draft": "我在雨棚投递板看到一条褪色的雨夜路线标记，它现在还在使用吗？",
		"position": Vector2(692, 276),
		"accent": "#e9945f",
	},
}

@onready var _ground: Node2D = $Ground
@onready var _world: Node2D = $World
@onready var _ui_layer: CanvasLayer = $Ui

var _player: TownPlayerController
var _npcs: Array[TownNpcActor] = []
var _prompt_label: Label
var _dialogue_panel: PanelContainer
var _dialogue_name: Label
var _dialogue_place: Label
var _history_label: RichTextLabel
var _relationship_label: Label
var _status_label: Label
var _dialogue_status_label: Label
var _message_input: LineEdit
var _send_button: Button
var _retry_button: Button
var _close_button: Button
var _health_retry_button: Button
var _mute_button: Button
var _topic_memory_button: Button
var _topic_memory_popup: PanelContainer
var _topic_memory_title: Label
var _topic_memory_buttons: Array[Button] = []
var _topic_memory_actions: GridContainer
var _topic_memory_confirmation: VBoxContainer
var _topic_memory_confirmation_label: Label
var _topic_memory_confirm_button: Button
var _topic_memory_cancel_button: Button
var _observation_card: PanelContainer
var _observation_title: Label
var _observation_body: Label
var _observation_target: Label
var _observation_close_button: Button
var _observation_remember_button: Button
var _pending_guided_action: Dictionary = {}
var _discovered_landmarks: Dictionary = {}
var _active_landmark_id: StringName = &""
var _observation_open := false
var _health_client: Node
var _dialogue_client: Node
var _relationship_client: Node
var _ambient_player: AudioStreamPlayer
var _ambient_playback: AudioStreamGeneratorPlayback
var _interaction_player: AudioStreamPlayer
var _ui_audio_player: AudioStreamPlayer
var _dialogue_open := false
var _backend_available := false
var _audio_muted := false
var _audio_runtime_enabled := false
var _ambient_phase := 0.0
var _ambient_value := 0.0
var _capture_path := ""
var _ui_font: Font


func _ready() -> void:
	_capture_path = _capture_argument()
	_ui_font = UI_FONT
	_build_ground()
	_build_landmarks()
	_build_boundaries()
	_spawn_npcs()
	_spawn_player()
	_build_ui()
	_build_dialogue_clients()
	_build_audio()
	if not _capture_path.is_empty():
		_set_health_state(&"connected")
		if _has_user_argument("--capture-observation-card"):
			_show_observation_capture_state()
		else:
			if _has_user_argument("--capture-context-topic-menu"):
				_discovered_landmarks[&"twilight_guide_board"] = true
			_open_dialogue(&"neon_guide")
			if (
				_has_user_argument("--capture-topic-menu")
				or _has_user_argument("--capture-context-topic-menu")
			):
				_set_topic_memory_popup_visible(true)
		_capture_after_render.call_deferred()
	elif _has_user_argument("--skip-health-check"):
		_set_health_state(&"unavailable")
	else:
		_start_health_check()


func _exit_tree() -> void:
	if is_instance_valid(_ambient_player):
		_ambient_player.stop()
	if is_instance_valid(_interaction_player):
		_interaction_player.stop()
	if is_instance_valid(_ui_audio_player):
		_ui_audio_player.stop()
	_ambient_playback = null


func _process(_delta: float) -> void:
	_fill_ambient()
	if _observation_open:
		return
	if not is_instance_valid(_player) or _dialogue_open:
		return
	var closest := nearest_interaction_target(_player.global_position, INTERACTION_DISTANCE)
	if closest.is_empty():
		_prompt_label.visible = false
		return
	_prompt_label.text = _prompt_for_target(closest)
	_prompt_label.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("close_dialogue") and _observation_open:
		_close_observation()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("close_dialogue") and _dialogue_open:
		_close_dialogue()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("interact") and not _dialogue_open and not _observation_open:
		var closest := nearest_interaction_target(_player.global_position, INTERACTION_DISTANCE)
		if not closest.is_empty():
			if StringName(closest["kind"]) == &"npc":
				_open_dialogue(StringName(closest["id"]))
			else:
				_open_observation(StringName(closest["id"]))
			get_viewport().set_input_as_handled()


func nearest_npc(origin: Vector2, maximum_distance: float) -> TownNpcActor:
	var best: TownNpcActor = null
	var best_distance := maximum_distance
	for npc: TownNpcActor in _npcs:
		var distance := origin.distance_to(npc.global_position)
		if distance < best_distance:
			best = npc
			best_distance = distance
	return best


func nearest_interaction_target(origin: Vector2, maximum_distance: float) -> Dictionary:
	var best: Dictionary = {}
	var best_distance := maximum_distance
	for npc: TownNpcActor in _npcs:
		var distance := origin.distance_to(npc.global_position)
		if distance < best_distance:
			best_distance = distance
			best = {
				"kind": &"npc",
				"id": StringName(npc.npc_id),
				"display_name": npc.display_name,
				"distance": distance,
			}
	for landmark_id: StringName in LANDMARK_PROFILES:
		var profile: Dictionary = LANDMARK_PROFILES[landmark_id]
		var distance: float = origin.distance_to(profile["position"])
		if distance < best_distance:
			best_distance = distance
			best = {
				"kind": &"landmark",
				"id": landmark_id,
				"display_name": String(profile["display_name"]),
				"distance": distance,
			}
	return best


func _prompt_for_target(target: Dictionary) -> String:
	if StringName(target.get("kind", &"")) == &"npc":
		return "E  与 %s 交谈" % String(target.get("display_name", ""))
	return "E  查看%s" % String(target.get("display_name", ""))


func approved_npc_ids() -> Array[StringName]:
	var ids: Array[StringName] = []
	for npc: TownNpcActor in _npcs:
		ids.append(StringName(npc.npc_id))
	return ids


func approved_landmark_ids() -> Array[StringName]:
	var ids: Array[StringName] = []
	for landmark_id: StringName in LANDMARK_PROFILES:
		ids.append(landmark_id)
	return ids


func is_dialogue_open() -> bool:
	return _dialogue_open


func open_dialogue_for_testing(npc_id: StringName) -> bool:
	return _open_dialogue(npc_id)


func close_dialogue_for_testing() -> void:
	_close_dialogue()


func open_observation_for_testing(landmark_id: StringName) -> bool:
	return _open_observation(landmark_id)


func close_observation_for_testing() -> void:
	_close_observation()


func remember_observation_for_testing() -> void:
	_remember_observation()


func is_observation_open() -> bool:
	return _observation_open


func has_discovered_landmark(landmark_id: StringName) -> bool:
	return bool(_discovered_landmarks.get(landmark_id, false))


func has_discovery_for_npc(npc_id: StringName) -> bool:
	var profile := _landmark_profile_for_npc(npc_id)
	return (
		not profile.is_empty()
		and bool(_discovered_landmarks.get(StringName(profile["landmark_id"]), false))
	)


func landmark_profile_for_testing(landmark_id: StringName) -> Dictionary:
	return (LANDMARK_PROFILES.get(landmark_id, {}) as Dictionary).duplicate(true)


func dialogue_client_for_testing() -> Node:
	return _dialogue_client


func relationship_client_for_testing() -> Node:
	return _relationship_client


func topic_profile_for_testing(npc_id: StringName) -> Dictionary:
	return (NPC_TOPIC_PROFILES.get(npc_id, {}) as Dictionary).duplicate(true)


func set_backend_available_for_testing(value: bool) -> void:
	_backend_available = value
	_update_dialogue_controls()


func player() -> TownPlayerController:
	return _player


func _build_ground() -> void:
	var grass := TextureRect.new()
	grass.name = "Grass"
	grass.position = Vector2.ZERO
	grass.size = WORLD_SIZE
	grass.texture = GRASS_TEXTURE
	grass.modulate = Color("#c58b79")
	grass.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	grass.stretch_mode = TextureRect.STRETCH_TILE
	grass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ground.add_child(grass)

	_add_ground_rect("StreetShadow", Rect2(0, 214, 960, 116), Color("#453348"))
	_add_ground_rect("Street", Rect2(0, 206, 960, 112), Color("#b77a55"))
	_add_ground_rect("StreetCenter", Rect2(0, 251, 960, 22), Color("#d69a64"))
	_add_ground_rect("PlazaShadow", Rect2(337, 125, 302, 272), Color("#49364f"))
	_add_ground_rect("Plaza", Rect2(345, 117, 286, 272), Color("#c58b68"))
	_add_ground_rect("PlazaInset", Rect2(361, 133, 254, 240), Color("#d5a071"))
	for x: int in range(378, 612, 28):
		_add_ground_rect("PlazaLine%d" % x, Rect2(x, 133, 2, 240), Color("#b77a55"))
	for y: int in range(151, 374, 28):
		_add_ground_rect("PlazaLine%d" % y, Rect2(361, y, 254, 2), Color("#b77a55"))


func _add_ground_rect(node_name: String, rect: Rect2, color: Color) -> void:
	var polygon := Polygon2D.new()
	polygon.name = node_name
	polygon.polygon = PackedVector2Array([
		rect.position,
		Vector2(rect.end.x, rect.position.y),
		rect.end,
		Vector2(rect.position.x, rect.end.y),
	])
	polygon.color = color
	_ground.add_child(polygon)


func _build_landmarks() -> void:
	_add_building("GuideHouse", Vector2(72, 26), Rect2(144, 0, 128, 128), 1.35)
	_add_building("ArchiveHouse", Vector2(395, 4), Rect2(144, 0, 128, 128), 1.55)
	_add_building("CourierHouse", Vector2(722, 36), Rect2(272, 16, 80, 112), 1.45)
	_add_tree_cluster(Vector2(8, 340))
	_add_tree_cluster(Vector2(835, 354))
	_add_tree_cluster(Vector2(654, 368))
	_add_neon_sign(Vector2(473, 119), Color("#70d6c8"), "SIGNAL")
	_add_neon_sign(Vector2(786, 173), Color("#e9945f"), "POST")
	_add_lamp(Vector2(285, 226))
	_add_lamp(Vector2(666, 226))
	for landmark_id: StringName in LANDMARK_PROFILES:
		_add_exploration_landmark(landmark_id, LANDMARK_PROFILES[landmark_id])
	_add_static_collision(Rect2(72, 86, 173, 105), "GuideHouseCollision")
	_add_static_collision(Rect2(395, 82, 198, 112), "ArchiveHouseCollision")
	_add_static_collision(Rect2(722, 104, 116, 88), "CourierHouseCollision")
	_add_static_collision(Rect2(8, 382, 120, 92), "TreeCollisionLeft")
	_add_static_collision(Rect2(835, 395, 108, 92), "TreeCollisionRight")


func _add_exploration_landmark(landmark_id: StringName, profile: Dictionary) -> void:
	var root := Node2D.new()
	root.name = "Landmark%s" % String(landmark_id).to_pascal_case()
	root.position = profile["position"]
	root.z_index = 1
	_world.add_child(root)

	var panel := ColorRect.new()
	panel.position = Vector2(-21, -27)
	panel.size = Vector2(42, 23)
	panel.color = Color("#2d263d")
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(panel)
	var accent := ColorRect.new()
	accent.position = Vector2(3, 3)
	accent.size = Vector2(36, 3)
	accent.color = Color(String(profile["accent"]))
	accent.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(accent)
	var mark := Label.new()
	mark.position = Vector2(0, 6)
	mark.size = Vector2(42, 15)
	mark.text = "◆"
	mark.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mark.add_theme_font_override("font", _ui_font)
	mark.add_theme_font_size_override("font_size", 10)
	mark.add_theme_color_override("font_color", Color(String(profile["accent"])))
	mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(mark)
	for x: float in [-15.0, 12.0]:
		var leg := ColorRect.new()
		leg.position = Vector2(x, -4)
		leg.size = Vector2(3, 10)
		leg.color = Color("#352b42")
		leg.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root.add_child(leg)
	var label := Label.new()
	label.position = Vector2(-42, 7)
	label.size = Vector2(84, 16)
	label.text = String(profile["short_label"])
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_override("font", _ui_font)
	label.add_theme_font_size_override("font_size", 9)
	label.add_theme_color_override("font_color", Color("#f3dbc1"))
	label.add_theme_color_override("font_shadow_color", Color("#171326"))
	label.add_theme_constant_override("shadow_offset_x", 1)
	label.add_theme_constant_override("shadow_offset_y", 1)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(label)
	_add_static_collision(
		Rect2(Vector2(profile["position"]) + Vector2(-21, -27), Vector2(42, 23)),
		"%sCollision" % root.name,
	)


func _add_building(node_name: String, position: Vector2, region: Rect2, scale_value: float) -> void:
	var atlas := AtlasTexture.new()
	atlas.atlas = TILESET_TEXTURE
	atlas.region = region
	var sprite := Sprite2D.new()
	sprite.name = node_name
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = atlas
	sprite.modulate = Color("#dfa184")
	sprite.centered = false
	sprite.position = position
	sprite.scale = Vector2.ONE * scale_value
	sprite.z_index = -2
	_world.add_child(sprite)


func _add_tree_cluster(position: Vector2) -> void:
	var atlas := AtlasTexture.new()
	atlas.atlas = TILESET_TEXTURE
	atlas.region = Rect2(64, 24, 80, 112)
	var sprite := Sprite2D.new()
	sprite.name = "TreeCluster"
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.texture = atlas
	sprite.modulate = Color("#bd877d")
	sprite.centered = false
	sprite.position = position
	sprite.scale = Vector2(1.45, 1.45)
	_world.add_child(sprite)


func _add_neon_sign(position: Vector2, color: Color, text: String) -> void:
	var panel := ColorRect.new()
	panel.name = "%sSign" % text.to_pascal_case()
	panel.position = position
	panel.size = Vector2(68, 20)
	panel.color = Color("#29233d")
	panel.z_index = 2
	_world.add_child(panel)
	var accent := ColorRect.new()
	accent.position = Vector2(3, 3)
	accent.size = Vector2(62, 2)
	accent.color = color
	panel.add_child(accent)
	var label := Label.new()
	label.position = Vector2(0, 3)
	label.size = Vector2(68, 17)
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_override("font", _ui_font)
	label.add_theme_font_size_override("font_size", 9)
	label.add_theme_color_override("font_color", color)
	panel.add_child(label)


func _add_lamp(position: Vector2) -> void:
	var pole := ColorRect.new()
	pole.position = position
	pole.size = Vector2(4, 42)
	pole.color = Color("#342944")
	_world.add_child(pole)
	var glow := Polygon2D.new()
	glow.position = position + Vector2(2, 2)
	glow.polygon = PackedVector2Array([Vector2(-18, 4), Vector2(18, 4), Vector2(34, 58), Vector2(-34, 58)])
	glow.color = Color(1.0, 0.68, 0.32, 0.12)
	glow.z_index = -1
	_world.add_child(glow)
	var light := ColorRect.new()
	light.position = position + Vector2(-3, -2)
	light.size = Vector2(10, 8)
	light.color = Color("#ffd07a")
	_world.add_child(light)


func _build_boundaries() -> void:
	_add_static_collision(Rect2(-16, -16, WORLD_SIZE.x + 32, 16), "NorthBoundary")
	_add_static_collision(Rect2(-16, WORLD_SIZE.y, WORLD_SIZE.x + 32, 16), "SouthBoundary")
	_add_static_collision(Rect2(-16, 0, 16, WORLD_SIZE.y), "WestBoundary")
	_add_static_collision(Rect2(WORLD_SIZE.x, 0, 16, WORLD_SIZE.y), "EastBoundary")


func _add_static_collision(rect: Rect2, node_name: String) -> void:
	var body := StaticBody2D.new()
	body.name = node_name
	body.collision_layer = 1
	body.collision_mask = 1
	body.position = rect.get_center()
	var shape_node := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	shape_node.shape = shape
	body.add_child(shape_node)
	_world.add_child(body)


func _spawn_npcs() -> void:
	_add_npc(&"neon_guide", "Nia", "入口导览点", Vector2(219, 268), 0)
	_add_npc(&"signal_archivist", "Ivo", "信号档案亭", Vector2(515, 244), 4)
	_add_npc(&"night_courier", "Rhea", "街尾投递点", Vector2(790, 276), 8)


func _add_npc(id: StringName, display_name: String, place: String, position: Vector2, frame: int) -> void:
	var npc := NPC_SCENE.instantiate() as TownNpcActor
	npc.name = display_name
	npc.npc_id = String(id)
	npc.display_name = display_name
	npc.place_label = place
	npc.sprite_frame = frame
	npc.position = position
	_world.add_child(npc)
	_npcs.append(npc)


func _spawn_player() -> void:
	_player = PLAYER_SCENE.instantiate() as TownPlayerController
	_player.position = Vector2(82, 280)
	_world.add_child(_player)


func _build_ui() -> void:
	var root := Control.new()
	root.name = "TownUi"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.theme = _create_theme()
	_ui_layer.add_child(root)

	var title := Label.new()
	title.name = "TownTitle"
	title.position = Vector2(238, 10)
	title.size = Vector2(164, 28)
	title.text = "暮光街区"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 16)
	title.add_theme_color_override("font_color", Color("#ffe0a6"))
	root.add_child(title)

	var status_panel := PanelContainer.new()
	status_panel.name = "HealthStatus"
	status_panel.position = Vector2(12, 12)
	status_panel.size = Vector2(210, 26)
	status_panel.add_theme_stylebox_override("panel", _panel_style(Color("#211b35e6"), Color("#6bc8b8"), 1))
	root.add_child(status_panel)
	var health_row := HBoxContainer.new()
	health_row.add_theme_constant_override("separation", 4)
	status_panel.add_child(health_row)
	_status_label = Label.new()
	_status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status_label.text = "● 正在连接对话服务"
	_status_label.add_theme_font_size_override("font_size", 10)
	_status_label.add_theme_color_override("font_color", Color("#d8e7dc"))
	health_row.add_child(_status_label)
	_health_retry_button = Button.new()
	_health_retry_button.name = "HealthRetryButton"
	_health_retry_button.text = "重试"
	_health_retry_button.add_theme_font_size_override("font_size", 9)
	_health_retry_button.visible = false
	_health_retry_button.pressed.connect(_retry_health_check)
	health_row.add_child(_health_retry_button)

	_prompt_label = Label.new()
	_prompt_label.name = "InteractionPrompt"
	_prompt_label.position = Vector2(220, 315)
	_prompt_label.size = Vector2(200, 30)
	_prompt_label.text = "E  与 Nia 交谈"
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.add_theme_font_size_override("font_size", 12)
	_prompt_label.add_theme_color_override("font_color", Color("#ffe0a6"))
	_prompt_label.add_theme_color_override("font_shadow_color", Color("#171326"))
	_prompt_label.add_theme_constant_override("shadow_offset_x", 1)
	_prompt_label.add_theme_constant_override("shadow_offset_y", 1)
	_prompt_label.visible = false
	root.add_child(_prompt_label)

	_dialogue_panel = PanelContainer.new()
	_dialogue_panel.name = "DialoguePanel"
	_dialogue_panel.position = Vector2(14, 218)
	_dialogue_panel.size = Vector2(612, 130)
	_dialogue_panel.add_theme_stylebox_override("panel", _panel_style(Color("#171326"), Color("#df915e"), 2))
	_dialogue_panel.visible = false
	root.add_child(_dialogue_panel)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	_dialogue_panel.add_child(margin)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	margin.add_child(row)

	var identity := VBoxContainer.new()
	identity.custom_minimum_size = Vector2(104, 0)
	identity.add_theme_constant_override("separation", 3)
	row.add_child(identity)
	_dialogue_name = Label.new()
	_dialogue_name.text = "Nia"
	_dialogue_name.add_theme_font_size_override("font_size", 20)
	_dialogue_name.add_theme_color_override("font_color", Color("#ffca7a"))
	identity.add_child(_dialogue_name)
	_dialogue_place = Label.new()
	_dialogue_place.text = "入口导览点"
	_dialogue_place.add_theme_font_size_override("font_size", 10)
	_dialogue_place.add_theme_color_override("font_color", Color("#aeb8c9"))
	identity.add_child(_dialogue_place)
	_relationship_label = Label.new()
	_relationship_label.text = "关系 · 初识"
	_relationship_label.add_theme_font_size_override("font_size", 10)
	_relationship_label.add_theme_color_override("font_color", Color("#72d7c2"))
	identity.add_child(_relationship_label)
	_mute_button = Button.new()
	_mute_button.name = "MuteButton"
	_mute_button.text = "声音：开"
	_mute_button.tooltip_text = "关闭本次游戏的环境声和提示音"
	_mute_button.add_theme_font_size_override("font_size", 9)
	_mute_button.pressed.connect(_toggle_audio)
	identity.add_child(_mute_button)

	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 5)
	row.add_child(content)
	_history_label = RichTextLabel.new()
	_history_label.name = "ConversationHistory"
	_history_label.text = "Nia：晚上好，访客。沿着灯火走，就能找到广场。"
	_history_label.custom_minimum_size = Vector2(0, 42)
	_history_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_history_label.fit_content = false
	_history_label.scroll_active = true
	_history_label.scroll_following = true
	_history_label.bbcode_enabled = false
	_history_label.add_theme_font_size_override("font_size", 11)
	_history_label.add_theme_color_override("font_color", Color("#eee6dc"))
	content.add_child(_history_label)

	var input_row := HBoxContainer.new()
	input_row.add_theme_constant_override("separation", 6)
	content.add_child(input_row)
	_message_input = LineEdit.new()
	_message_input.name = "MessageInput"
	_message_input.placeholder_text = "输入想说的话…"
	_message_input.max_length = 1000
	_message_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_message_input.add_theme_font_size_override("font_size", 11)
	_message_input.text_changed.connect(_on_message_changed)
	_message_input.gui_input.connect(_on_message_input)
	input_row.add_child(_message_input)
	_send_button = Button.new()
	_send_button.name = "SendButton"
	_send_button.text = "发送"
	_send_button.disabled = true
	_send_button.pressed.connect(_send_message)
	input_row.add_child(_send_button)
	_retry_button = Button.new()
	_retry_button.name = "RetryButton"
	_retry_button.text = "重试"
	_retry_button.visible = false
	_retry_button.pressed.connect(_retry_dialogue)
	input_row.add_child(_retry_button)
	_close_button = Button.new()
	_close_button.name = "CloseButton"
	_close_button.text = "关闭 Esc"
	_close_button.pressed.connect(_close_dialogue)
	input_row.add_child(_close_button)
	_dialogue_status_label = Label.new()
	_dialogue_status_label.name = "DialogueStatus"
	_dialogue_status_label.text = "可以开始交谈 · Ctrl+Enter 发送"
	_dialogue_status_label.add_theme_font_size_override("font_size", 9)
	_dialogue_status_label.add_theme_color_override("font_color", Color("#8f99aa"))
	content.add_child(_dialogue_status_label)

	_topic_memory_button = Button.new()
	_topic_memory_button.name = "TopicMemoryButton"
	_topic_memory_button.text = "话题与记忆"
	_topic_memory_button.tooltip_text = "打开当前 NPC 的引导话题和记忆动作"
	_topic_memory_button.add_theme_font_size_override("font_size", 9)
	_topic_memory_button.pressed.connect(_toggle_topic_memory_popup)
	input_row.add_child(_topic_memory_button)

	_build_topic_memory_popup(root)
	_build_observation_card(root)


func _build_observation_card(root: Control) -> void:
	_observation_card = PanelContainer.new()
	_observation_card.name = "ObservationCard"
	_observation_card.position = Vector2(246, 72)
	_observation_card.size = Vector2(380, 154)
	_observation_card.add_theme_stylebox_override(
		"panel",
		_panel_style(Color("#211b35f7"), Color("#70d6c8"), 2),
	)
	_observation_card.visible = false
	root.add_child(_observation_card)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 9)
	margin.add_theme_constant_override("margin_bottom", 9)
	_observation_card.add_child(margin)

	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 5)
	margin.add_child(content)

	var eyebrow := Label.new()
	eyebrow.text = "街区发现"
	eyebrow.add_theme_font_size_override("font_size", 9)
	eyebrow.add_theme_color_override("font_color", Color("#70d6c8"))
	content.add_child(eyebrow)

	_observation_title = Label.new()
	_observation_title.name = "ObservationTitle"
	_observation_title.text = "暮光导览牌"
	_observation_title.add_theme_font_size_override("font_size", 16)
	_observation_title.add_theme_color_override("font_color", Color("#ffca7a"))
	content.add_child(_observation_title)

	_observation_body = Label.new()
	_observation_body.name = "ObservationBody"
	_observation_body.text = "导览牌标出一条只在傍晚亮起的夜市灯带。"
	_observation_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_observation_body.add_theme_font_size_override("font_size", 11)
	_observation_body.add_theme_color_override("font_color", Color("#eee6dc"))
	content.add_child(_observation_body)

	var action_row := HBoxContainer.new()
	action_row.add_theme_constant_override("separation", 6)
	content.add_child(action_row)
	_observation_target = Label.new()
	_observation_target.name = "ObservationTarget"
	_observation_target.text = "可带去和 Nia 讨论"
	_observation_target.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_observation_target.add_theme_font_size_override("font_size", 9)
	_observation_target.add_theme_color_override("font_color", Color("#aeb8c9"))
	action_row.add_child(_observation_target)
	_observation_close_button = Button.new()
	_observation_close_button.name = "ObservationCloseButton"
	_observation_close_button.text = "关闭 Esc"
	_observation_close_button.add_theme_font_size_override("font_size", 9)
	_observation_close_button.pressed.connect(_close_observation)
	action_row.add_child(_observation_close_button)
	_observation_remember_button = Button.new()
	_observation_remember_button.name = "ObservationRememberButton"
	_observation_remember_button.text = "记下话题"
	_observation_remember_button.add_theme_font_size_override("font_size", 9)
	_observation_remember_button.pressed.connect(_remember_observation)
	action_row.add_child(_observation_remember_button)


func _show_observation_capture_state() -> void:
	_player.position = Vector2(174, 270)
	_open_observation(&"twilight_guide_board")
	_prompt_label.text = "E  查看暮光导览牌"
	_prompt_label.visible = true


func _open_observation(landmark_id: StringName) -> bool:
	if (
		_dialogue_open
		or _observation_open
		or not LANDMARK_PROFILES.has(landmark_id)
		or _dialogue_client.is_request_in_flight()
	):
		return false
	var profile: Dictionary = LANDMARK_PROFILES[landmark_id]
	_active_landmark_id = landmark_id
	_observation_open = true
	_observation_title.text = String(profile["display_name"])
	_observation_body.text = String(profile["observation"])
	var remembered := bool(_discovered_landmarks.get(landmark_id, false))
	_observation_target.text = "%s可带去和 %s 讨论" % [
		"已记下 · " if remembered else "",
		String(profile["npc_name"]),
	]
	_observation_remember_button.text = "已记下" if remembered else "记下话题"
	_observation_remember_button.disabled = remembered
	_observation_card.visible = true
	_prompt_label.text = "E  查看%s" % String(profile["display_name"])
	_prompt_label.visible = true
	_player.set_movement_locked(true)
	_play_interaction_sound()
	return true


func _close_observation() -> void:
	if not _observation_open:
		return
	_observation_open = false
	_active_landmark_id = &""
	_observation_card.visible = false
	_prompt_label.visible = false
	if is_instance_valid(_player):
		_player.set_movement_locked(false)
	_play_ui_sound()


func _remember_observation() -> void:
	if not _observation_open or not LANDMARK_PROFILES.has(_active_landmark_id):
		return
	_discovered_landmarks[_active_landmark_id] = true
	var profile: Dictionary = LANDMARK_PROFILES[_active_landmark_id]
	_observation_target.text = "已记下 · 可带去和 %s 讨论" % String(profile["npc_name"])
	_observation_remember_button.text = "已记下"
	_observation_remember_button.disabled = true
	_play_ui_sound()


func _landmark_profile_for_npc(npc_id: StringName) -> Dictionary:
	for landmark_id: StringName in LANDMARK_PROFILES:
		var profile: Dictionary = LANDMARK_PROFILES[landmark_id]
		if StringName(profile["npc_id"]) == npc_id:
			var result := profile.duplicate(true)
			result["landmark_id"] = landmark_id
			return result
	return {}


func _build_topic_memory_popup(root: Control) -> void:
	_topic_memory_popup = PanelContainer.new()
	_topic_memory_popup.name = "TopicMemoryPopup"
	_topic_memory_popup.position = Vector2(236, 52)
	_topic_memory_popup.size = Vector2(390, 160)
	_topic_memory_popup.add_theme_stylebox_override(
		"panel",
		_panel_style(Color("#211b35f7"), Color("#df915e"), 2),
	)
	_topic_memory_popup.visible = false
	root.add_child(_topic_memory_popup)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_bottom", 8)
	_topic_memory_popup.add_child(margin)

	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 4)
	margin.add_child(content)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 6)
	content.add_child(header)
	_topic_memory_title = Label.new()
	_topic_memory_title.name = "TopicMemoryTitle"
	_topic_memory_title.text = "Nia · 话题与记忆"
	_topic_memory_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_topic_memory_title.add_theme_font_size_override("font_size", 13)
	_topic_memory_title.add_theme_color_override("font_color", Color("#ffca7a"))
	header.add_child(_topic_memory_title)
	var collapse := Button.new()
	collapse.name = "TopicMemoryCollapseButton"
	collapse.text = "收起"
	collapse.add_theme_font_size_override("font_size", 9)
	collapse.pressed.connect(_toggle_topic_memory_popup)
	header.add_child(collapse)

	var hint := Label.new()
	hint.name = "TopicMemoryHint"
	hint.text = "选择引导动作 · 状态写入前会再次确认"
	hint.add_theme_font_size_override("font_size", 9)
	hint.add_theme_color_override("font_color", Color("#aeb8c9"))
	content.add_child(hint)

	_topic_memory_actions = GridContainer.new()
	_topic_memory_actions.name = "TopicMemoryActions"
	_topic_memory_actions.columns = 2
	_topic_memory_actions.add_theme_constant_override("h_separation", 5)
	_topic_memory_actions.add_theme_constant_override("v_separation", 3)
	content.add_child(_topic_memory_actions)
	for index: int in range(7):
		var action := Button.new()
		action.name = "TopicAction%d" % index
		action.custom_minimum_size = Vector2(180, 22)
		action.add_theme_font_size_override("font_size", 9)
		action.focus_mode = Control.FOCUS_NONE
		action.pressed.connect(_on_topic_memory_action.bind(index))
		_topic_memory_actions.add_child(action)
		_topic_memory_buttons.append(action)

	_topic_memory_confirmation = VBoxContainer.new()
	_topic_memory_confirmation.name = "TopicMemoryConfirmation"
	_topic_memory_confirmation.add_theme_constant_override("separation", 6)
	_topic_memory_confirmation.visible = false
	content.add_child(_topic_memory_confirmation)
	_topic_memory_confirmation_label = Label.new()
	_topic_memory_confirmation_label.name = "TopicMemoryConfirmationText"
	_topic_memory_confirmation_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_topic_memory_confirmation_label.add_theme_font_size_override("font_size", 10)
	_topic_memory_confirmation_label.add_theme_color_override("font_color", Color("#eee6dc"))
	_topic_memory_confirmation.add_child(_topic_memory_confirmation_label)
	var confirmation_actions := HBoxContainer.new()
	confirmation_actions.alignment = BoxContainer.ALIGNMENT_END
	confirmation_actions.add_theme_constant_override("separation", 6)
	_topic_memory_confirmation.add_child(confirmation_actions)
	_topic_memory_cancel_button = Button.new()
	_topic_memory_cancel_button.name = "TopicMemoryCancelButton"
	_topic_memory_cancel_button.text = "取消"
	_topic_memory_cancel_button.pressed.connect(_cancel_guided_action)
	confirmation_actions.add_child(_topic_memory_cancel_button)
	_topic_memory_confirm_button = Button.new()
	_topic_memory_confirm_button.name = "TopicMemoryConfirmButton"
	_topic_memory_confirm_button.text = "确认发送"
	_topic_memory_confirm_button.pressed.connect(_confirm_guided_action)
	confirmation_actions.add_child(_topic_memory_confirm_button)


func _toggle_topic_memory_popup() -> void:
	_set_topic_memory_popup_visible(not _topic_memory_popup.visible)
	_play_ui_sound()


func _set_topic_memory_popup_visible(value: bool) -> void:
	if not _dialogue_open:
		value = false
	_topic_memory_popup.visible = value
	if value:
		_cancel_guided_action(false)
		_render_topic_memory_popup()


func _render_topic_memory_popup() -> void:
	var npc_id := StringName(_dialogue_client.active_npc_id())
	var profile: Dictionary = NPC_TOPIC_PROFILES.get(npc_id, {})
	if profile.is_empty():
		_set_topic_memory_popup_visible(false)
		return
	var display_name := String(profile["display_name"])
	var topic := String(profile["topic"])
	_topic_memory_title.text = "%s · 话题与记忆" % display_name
	var labels := [
		"聊聊 · %s" % topic,
		"记住 · %s" % topic,
		"问问是否记得",
		"回复简洁",
		"回复自然",
		"忘记这个主题",
		"讨论街区发现",
	]
	var landmark_profile := _landmark_profile_for_npc(npc_id)
	var discovery_available := (
		not landmark_profile.is_empty()
		and bool(
			_discovered_landmarks.get(StringName(landmark_profile["landmark_id"]), false)
		)
	)
	for index: int in range(_topic_memory_buttons.size()):
		_topic_memory_buttons[index].text = labels[index]
		_topic_memory_buttons[index].visible = index < 6 or discovery_available


func _on_topic_memory_action(index: int) -> void:
	if _dialogue_client.is_request_in_flight():
		return
	var npc_id := StringName(_dialogue_client.active_npc_id())
	var profile: Dictionary = NPC_TOPIC_PROFILES.get(npc_id, {})
	if profile.is_empty():
		return
	var display_name := String(profile["display_name"])
	var topic := String(profile["topic"])
	match index:
		0:
			_fill_guided_draft(String(profile["draft"]))
		2:
			_fill_guided_draft("你还记得我喜欢的%s吗？" % topic)
		1:
			_show_guided_confirmation(
				{
					"kind": "remember_topic",
					"raw": "请记住：favorite_cyber_town_topic=%s" % topic,
					"display": "请记住我喜欢%s" % topic,
					"success": "%s 已记下你喜欢“%s”。" % [display_name, topic],
					"confirmation": "让 %s 记住：你喜欢“%s”？" % [display_name, topic],
				}
			)
		3:
			_show_guided_confirmation(
				{
					"kind": "reply_style",
					"raw": "请记住：reply_style=concise",
					"display": "请用简洁方式回复我",
					"success": "%s 已将回复方式设为简洁。" % display_name,
					"confirmation": "将 %s 的后续回复设为一至两句？" % display_name,
				}
			)
		4:
			_show_guided_confirmation(
				{
					"kind": "reply_style",
					"raw": "请记住：reply_style=balanced",
					"display": "请用自然方式回复我",
					"success": "%s 已将回复方式设为自然。" % display_name,
					"confirmation": "将 %s 的后续回复恢复为自然节奏？" % display_name,
				}
			)
		5:
			_show_guided_confirmation(
				{
					"kind": "forget_topic",
					"raw": "请忘记：favorite_cyber_town_topic",
					"display": "请忘记我喜欢的%s" % topic,
					"success": "%s 已忘记你保存的“%s”主题。" % [display_name, topic],
					"confirmation": "让 %s 忘记你保存的“%s”主题？" % [display_name, topic],
				}
			)
		6:
			var landmark_profile := _landmark_profile_for_npc(npc_id)
			if (
				landmark_profile.is_empty()
				or not bool(
					_discovered_landmarks.get(
						StringName(landmark_profile["landmark_id"]),
						false,
					)
				)
			):
				return
			_fill_guided_draft(String(landmark_profile["discussion_draft"]))


func _fill_guided_draft(draft: String) -> void:
	_message_input.text = draft
	_message_input.caret_column = draft.length()
	_on_message_changed(draft)
	_set_topic_memory_popup_visible(false)
	_message_input.grab_focus()


func _show_guided_confirmation(action: Dictionary) -> void:
	_pending_guided_action = action.duplicate(true)
	_topic_memory_actions.visible = false
	_topic_memory_confirmation.visible = true
	_topic_memory_confirmation_label.text = String(action["confirmation"])


func _cancel_guided_action(play_sound := true) -> void:
	_pending_guided_action = {}
	if is_instance_valid(_topic_memory_actions):
		_topic_memory_actions.visible = true
	if is_instance_valid(_topic_memory_confirmation):
		_topic_memory_confirmation.visible = false
	if play_sound:
		_play_ui_sound()


func _confirm_guided_action() -> void:
	if (
		_pending_guided_action.is_empty()
		or not _backend_available
		or _dialogue_client.is_request_in_flight()
	):
		return
	if _dialogue_client.begin_send(
		String(_pending_guided_action["raw"]),
		String(_pending_guided_action["display"]),
		String(_pending_guided_action["kind"]),
		String(_pending_guided_action["success"]),
	):
		_play_ui_sound()
		_message_input.text = ""
		_update_dialogue_controls()


func _create_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font = _ui_font
	theme.default_font_size = 11
	var button_normal := _panel_style(Color("#3c3151"), Color("#80658e"), 1)
	var button_hover := _panel_style(Color("#58405d"), Color("#e89961"), 1)
	var button_disabled := _panel_style(Color("#29233a"), Color("#4f465d"), 1)
	theme.set_stylebox("normal", "Button", button_normal)
	theme.set_stylebox("hover", "Button", button_hover)
	theme.set_stylebox("pressed", "Button", button_hover)
	theme.set_stylebox("disabled", "Button", button_disabled)
	theme.set_color("font_color", "Button", Color("#fff0d1"))
	theme.set_color("font_disabled_color", "Button", Color("#817889"))
	theme.set_stylebox("normal", "LineEdit", _panel_style(Color("#211b32"), Color("#695776"), 1))
	theme.set_stylebox("focus", "LineEdit", _panel_style(Color("#211b32"), Color("#df915e"), 1))
	theme.set_color("font_color", "LineEdit", Color("#f4ecdf"))
	theme.set_color("font_placeholder_color", "LineEdit", Color("#80788a"))
	return theme


func _panel_style(background: Color, border: Color, border_width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(border_width)
	style.corner_radius_top_left = 2
	style.corner_radius_top_right = 2
	style.corner_radius_bottom_left = 2
	style.corner_radius_bottom_right = 2
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 5
	style.content_margin_bottom = 5
	return style


func _open_dialogue(npc_id: StringName) -> bool:
	if npc_id not in APPROVED_NPC_IDS:
		return false
	if _observation_open or _dialogue_client.is_request_in_flight():
		return false
	var target: TownNpcActor = null
	for npc: TownNpcActor in _npcs:
		if StringName(npc.npc_id) == npc_id:
			target = npc
			break
	if target == null:
		return false
	if not _dialogue_client.switch_npc(String(npc_id)):
		return false
	if not _relationship_client.switch_npc(String(npc_id)):
		return false
	_dialogue_open = true
	_dialogue_panel.visible = true
	_set_topic_memory_popup_visible(false)
	_prompt_label.visible = false
	_player.set_movement_locked(true)
	_dialogue_name.text = target.display_name
	_dialogue_place.text = target.place_label
	_play_interaction_sound()
	_message_input.placeholder_text = "输入想对%s说的话…" % target.display_name
	_message_input.text = ""
	_cancel_guided_action(false)
	_render_history()
	_render_relationship()
	_on_dialogue_state_changed(_dialogue_client.state)
	if not _capture_path.is_empty():
		_dialogue_status_label.text = "可以开始交谈 · Ctrl+Enter 发送"
	elif _backend_available:
		_relationship_client.refresh()
	else:
		_dialogue_status_label.text = "对话服务暂不可用，请先在顶部重试连接"
	return true


func _close_dialogue() -> void:
	if is_instance_valid(_dialogue_client) and _dialogue_client.is_request_in_flight():
		return
	_dialogue_open = false
	_dialogue_panel.visible = false
	_set_topic_memory_popup_visible(false)
	if is_instance_valid(_player):
		_player.set_movement_locked(false)


func _preview_line(npc_id: StringName) -> String:
	if _relationship_client.has_verified_snapshot and _relationship_client.state == &"available":
		var stage := String(_relationship_client.stage)
		var relationship_lines := {
			&"neon_guide": {
				"newcomer": "晚上好，访客。沿着灯火走，就能找到广场。",
				"acquaintance": "又见面了。今晚想从哪段灯火开始？",
				"friend": "你来了。今晚也一起慢慢看看街区吧。",
				"trusted_ally": "你来了，可信的伙伴。今晚也一起看看街区吧。",
			},
			&"signal_archivist": {
				"newcomer": "档案亭还亮着。你想查找哪一段信号？",
				"acquaintance": "又来查档案了？今晚想听哪一段记录？",
				"friend": "你来得正好，我正想和你聊一段小镇记录。",
				"trusted_ally": "可靠的伙伴，档案亭今晚也欢迎你。",
			},
			&"night_courier": {
				"newcomer": "街尾的最后一封信刚刚抵达。",
				"acquaintance": "又见面了。今晚的投递还算顺利。",
				"friend": "你来了。陪我在街尾歇一会儿吧。",
				"trusted_ally": "可信的伙伴，见到你让我安心。",
			},
		}
		var npc_lines: Dictionary = relationship_lines.get(npc_id, {})
		if npc_lines.has(stage):
			return String(npc_lines[stage])
	match npc_id:
		&"signal_archivist":
			return "档案亭还亮着。你想查找哪一段信号？"
		&"night_courier":
			return "街尾的最后一封信刚刚抵达。"
		_:
			return "晚上好，访客。沿着灯火走，就能找到广场。"


func _build_dialogue_clients() -> void:
	var base_url := _base_url_argument()
	_dialogue_client = Node.new()
	_dialogue_client.name = "DialogueClient"
	_dialogue_client.set_script(DIALOGUE_CLIENT_SCRIPT)
	var dialogue_request := HTTPRequest.new()
	dialogue_request.name = "HTTPRequest"
	_dialogue_client.add_child(dialogue_request)
	add_child(_dialogue_client)
	_dialogue_client.dialogue_url = base_url + "/api/v1/dialogue"
	_dialogue_client.state_changed.connect(_on_dialogue_state_changed)

	_relationship_client = Node.new()
	_relationship_client.name = "RelationshipClient"
	_relationship_client.set_script(RELATIONSHIP_CLIENT_SCRIPT)
	var relationship_request := HTTPRequest.new()
	relationship_request.name = "HTTPRequest"
	_relationship_client.add_child(relationship_request)
	add_child(_relationship_client)
	_relationship_client.relationship_url = base_url + "/api/v1/relationships"
	_relationship_client.snapshot_changed.connect(_on_relationship_snapshot_changed)


func _send_message() -> void:
	if not _dialogue_open or not _backend_available or _dialogue_client.is_request_in_flight():
		return
	if _dialogue_client.begin_send(_message_input.text):
		_play_ui_sound()
		_message_input.text = ""


func _retry_dialogue() -> void:
	if not _dialogue_open or not _backend_available:
		return
	if _dialogue_client.retry():
		_play_ui_sound()


func _on_message_changed(message: String) -> void:
	_dialogue_client.notify_input_changed(message)
	_update_dialogue_controls()


func _on_message_input(event: InputEvent) -> void:
	if (
		event is InputEventKey
		and event.pressed
		and not event.echo
		and event.ctrl_pressed
		and event.keycode in [KEY_ENTER, KEY_KP_ENTER]
	):
		_send_message()
		_message_input.accept_event()


func _on_dialogue_state_changed(next_state: StringName) -> void:
	if not _dialogue_open:
		return
	match next_state:
		&"loading":
			_dialogue_status_label.text = "%s 正在回应…" % _dialogue_name.text
		&"retrying":
			_dialogue_status_label.text = "正在重试…"
		&"success":
			_render_history()
			if _dialogue_client.latest_status == "degraded":
				_dialogue_status_label.text = "临时回应，不会加入短期记忆"
			else:
				_dialogue_status_label.text = "回复已收到"
			if not _pending_guided_action.is_empty():
				_set_topic_memory_popup_visible(false)
			_relationship_client.refresh(_dialogue_client.latest_request_id())
		&"timeout":
			_dialogue_status_label.text = "等待超时，请手动重试"
		&"unavailable":
			_dialogue_status_label.text = "对话服务暂不可用，请手动重试"
		&"invalid_response":
			_dialogue_status_label.text = "收到无效回复，请手动重试"
		&"unsafe":
			_dialogue_status_label.text = "这条消息无法处理"
		&"validation":
			_dialogue_status_label.text = "请输入 1–1000 个字符"
		_:
			_dialogue_status_label.text = (
				"可以开始交谈 · Ctrl+Enter 发送"
				if _backend_available or not _capture_path.is_empty()
				else "对话服务暂不可用，请先在顶部重试连接"
			)
	_update_dialogue_controls()


func _render_history() -> void:
	var turns: Array[Dictionary] = _dialogue_client.history()
	if turns.is_empty():
		_history_label.text = "%s：%s" % [
			_dialogue_name.text,
			_preview_line(StringName(_dialogue_client.active_npc_id())),
		]
		return
	var lines: PackedStringArray = []
	for turn: Dictionary in turns:
		lines.append("你：%s" % String(turn["message"]))
		var suffix := "（临时回应）" if bool(turn["degraded"]) else ""
		var speaker := (
			"系统"
			if String(turn.get("action_kind", "dialogue")) != "dialogue" and not bool(turn["degraded"])
			else _dialogue_name.text
		)
		lines.append("%s：%s%s" % [speaker, String(turn["reply"]), suffix])
	_history_label.text = "\n".join(lines)
	_history_label.scroll_to_line(maxi(0, lines.size() - 1))


func _update_dialogue_controls() -> void:
	if not is_instance_valid(_dialogue_client):
		return
	var waiting: bool = _dialogue_client.is_request_in_flight()
	_message_input.editable = not waiting
	_send_button.disabled = (
		waiting or not _backend_available or _message_input.text.strip_edges().is_empty()
	)
	_retry_button.visible = _dialogue_client.can_retry()
	_retry_button.disabled = waiting or not _backend_available
	_close_button.disabled = waiting
	_topic_memory_button.disabled = waiting
	for button: Button in _topic_memory_buttons:
		button.disabled = waiting
	_topic_memory_confirm_button.disabled = waiting or not _backend_available
	_topic_memory_cancel_button.disabled = waiting


func _on_relationship_snapshot_changed(_next_state: StringName) -> void:
	if _dialogue_open:
		_render_relationship()
		if _dialogue_client.history().is_empty():
			_render_history()


func _render_relationship() -> void:
	if _relationship_client.state == &"loading":
		_relationship_label.text = "关系 · 获取中"
		return
	if _relationship_client.state == &"unavailable" or not _relationship_client.has_verified_snapshot:
		_relationship_label.text = "关系 · 暂不可用" if _relationship_client.state == &"unavailable" else "关系 · 获取中"
		return
	var names := {
		"newcomer": "初识",
		"acquaintance": "相识",
		"friend": "朋友",
		"trusted_ally": "可信伙伴",
	}
	var stage_name: String = names.get(_relationship_client.stage, "暂不可用")
	var text := "关系 · %s" % stage_name
	if _relationship_client.has_verified_snapshot and not _relationship_client.latest_event.is_empty():
		var delta := int(_relationship_client.latest_event.get("applied_delta", 0))
		if delta > 0:
			text += " · 关系升温"
		elif delta < 0:
			text += " · 关系降温"
	_relationship_label.text = text


func _build_audio() -> void:
	_audio_runtime_enabled = DisplayServer.get_name() != "headless"
	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.name = "AmbientAudio"
	_ambient_player.volume_db = -34.0
	var generator := AudioStreamGenerator.new()
	generator.mix_rate = 22050.0
	generator.buffer_length = 0.5
	_ambient_player.stream = generator
	add_child(_ambient_player)
	if _audio_runtime_enabled:
		_ambient_player.play()
		_ambient_playback = _ambient_player.get_stream_playback() as AudioStreamGeneratorPlayback

	_interaction_player = AudioStreamPlayer.new()
	_interaction_player.name = "InteractionAudio"
	_interaction_player.stream = INTERACTION_SOUND
	_interaction_player.volume_db = -16.0
	add_child(_interaction_player)

	_ui_audio_player = AudioStreamPlayer.new()
	_ui_audio_player.name = "UiAudio"
	_ui_audio_player.stream = BUTTON_SOUND
	_ui_audio_player.volume_db = -18.0
	add_child(_ui_audio_player)


func _fill_ambient() -> void:
	if not _audio_runtime_enabled or _audio_muted or not is_instance_valid(_ambient_playback):
		return
	var frames := mini(_ambient_playback.get_frames_available(), 2048)
	for _index: int in range(frames):
		_ambient_phase = fmod(_ambient_phase + 1.0 / 22050.0, 1.0)
		_ambient_value = lerpf(_ambient_value, randf_range(-0.08, 0.08), 0.004)
		var distant_hum := sin(_ambient_phase * TAU * 55.0) * 0.035
		var sample := _ambient_value + distant_hum
		_ambient_playback.push_frame(Vector2(sample, sample))


func _toggle_audio() -> void:
	_audio_muted = not _audio_muted
	_mute_button.text = "声音：关" if _audio_muted else "声音：开"
	_ambient_player.stream_paused = _audio_muted
	if _audio_muted:
		_interaction_player.stop()
		_ui_audio_player.stop()
	else:
		_play_ui_sound()


func _play_interaction_sound() -> void:
	if _audio_runtime_enabled and not _audio_muted and is_instance_valid(_interaction_player):
		_interaction_player.play()


func _play_ui_sound() -> void:
	if _audio_runtime_enabled and not _audio_muted and is_instance_valid(_ui_audio_player):
		_ui_audio_player.play()


func _start_health_check() -> void:
	_health_client = Node.new()
	_health_client.name = "BackendHealthClient"
	_health_client.set_script(HEALTH_CLIENT_SCRIPT)
	var request := HTTPRequest.new()
	request.name = "HTTPRequest"
	_health_client.add_child(request)
	add_child(_health_client)
	_health_client.health_url = _base_url_argument() + "/api/v1/health"
	_health_client.state_changed.connect(_set_health_state)
	_health_client.call_deferred("begin_check", false)


func _set_health_state(state: StringName) -> void:
	_backend_available = state == &"connected"
	match state:
		&"connected":
			_status_label.text = "● 对话服务已连接"
			_status_label.add_theme_color_override("font_color", Color("#8ce0c2"))
			_health_retry_button.visible = false
			if _dialogue_open:
				_on_dialogue_state_changed(_dialogue_client.state)
				_relationship_client.refresh()
		&"connecting", &"retry":
			_status_label.text = "● 正在连接对话服务"
			_status_label.add_theme_color_override("font_color", Color("#ffd28a"))
			_health_retry_button.visible = false
		_:
			_status_label.text = "● 离线探索 · 对话暂不可用"
			_status_label.add_theme_color_override("font_color", Color("#e99a82"))
			_health_retry_button.visible = true
			if _dialogue_open and not _dialogue_client.is_request_in_flight():
				_dialogue_status_label.text = "对话服务暂不可用，请先在顶部重试连接"
	_update_dialogue_controls()


func _retry_health_check() -> void:
	if is_instance_valid(_health_client):
		_health_client.begin_check(true)


func _capture_argument() -> String:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			return argument.trim_prefix("--capture=")
	return ""


func _base_url_argument() -> String:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--base-url="):
			return argument.trim_prefix("--base-url=").trim_suffix("/")
	return "http://127.0.0.1:8000"


func _has_user_argument(expected: String) -> bool:
	return expected in OS.get_cmdline_user_args()


func _capture_after_render() -> void:
	for _frame: int in range(8):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var error := image.save_png(_capture_path)
	if error == OK:
		print("TOWN_CAPTURE=PASS path=%s" % _capture_path)
		get_tree().quit(0)
	else:
		printerr("TOWN_CAPTURE=FAIL error=%d" % error)
		get_tree().quit(1)
