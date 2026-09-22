class_name TownNpcActor
extends Area2D

@export var npc_id := ""
@export var display_name := ""
@export var place_label := ""
@export_range(0, 11, 1) var sprite_frame := 0

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _name_label: Label = $NameLabel
@onready var _place_label: Label = $PlaceLabel

var _base_sprite_y := -16.0
var _elapsed := 0.0


func _ready() -> void:
	_sprite.frame = sprite_frame
	_name_label.text = display_name
	_place_label.text = place_label
	_base_sprite_y = _sprite.position.y


func _process(delta: float) -> void:
	_elapsed += delta
	_sprite.position.y = _base_sprite_y + roundf(sin(_elapsed * 2.2))
