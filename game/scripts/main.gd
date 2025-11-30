extends Control
## Main script for the Castadi Game.
##
## This serves as the entry point and main controller for the game.


func _ready() -> void:
	var start_button: Button = $VBoxContainer/StartButton
	start_button.pressed.connect(_on_start_button_pressed)


func _on_start_button_pressed() -> void:
	print("Game started!")
