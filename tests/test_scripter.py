"""Tests for the scripter module."""
import pytest
from castadi import scripter as s


class TestCharacter:
    """Tests for the Character class."""

    def test_character_creation(self):
        """Test basic character creation."""
        char = s.Character("misty", "red hair, female")
        assert char.name == "misty"
        assert char.tags == "red hair, female"
        assert char.bubble_props is None

    def test_character_with_bubble_props(self):
        """Test character creation with bubble properties."""
        bubble_props = (24, (20, 20, 20), "white", "Arial.ttf")
        char = s.Character("popo", "male, dark hair", bubble_props)
        assert char.name == "popo"
        assert char.tags == "male, dark hair"
        assert char.bubble_props == bubble_props


class TestEvent:
    """Tests for the Event class."""

    def test_event_without_character(self):
        """Test event creation without a character."""
        event = s.Event("walking, happy")
        assert event.text == "walking, happy"
        assert event.character is None

    def test_event_with_character(self):
        """Test event creation with a character."""
        event = s.Event("Hello!", "misty")
        assert event.text == "Hello!"
        assert event.character is not None
        assert event.character.name == "misty"

    def test_bake_without_character_tags(self):
        """Test baking an event without character tags."""
        event = s.Event("walking, happy")
        result = event.bake({})
        assert result == "walking, happy"

    def test_bake_with_character_tags(self):
        """Test baking an event with character tags."""
        event = s.Event("[misty] walking, happy")
        characters = {"misty": s.Character("misty", "red hair, female")}
        result = event.bake(characters)
        assert result == "red hair, female walking, happy"

    def test_bake_removes_trailing_period(self):
        """Test that bake removes trailing periods."""
        event = s.Event("walking, happy.")
        result = event.bake({})
        assert result == "walking, happy"

    def test_bubble_without_character(self):
        """Test bubble returns None when no character."""
        event = s.Event("walking, happy")
        assert event.bubble() is None

    def test_bubble_with_character_no_props(self):
        """Test bubble with character but no bubble props."""
        event = s.Event("Hello!", "misty")
        bubble = event.bubble()
        assert bubble is not None
        assert bubble[0] == "Hello!"
        assert bubble[1:] == (None, None, None, None)

    def test_bubble_with_character_and_props(self):
        """Test bubble with character that has bubble props."""
        bubble_props = (24, (20, 20, 20), "white", "Arial.ttf")
        char = s.Character("misty", "red hair", bubble_props)
        event = s.Event("Hello!", "misty")
        event.character = char
        bubble = event.bubble()
        assert bubble[0] == "Hello!"
        assert bubble[1:] == bubble_props


class TestPanel:
    """Tests for the Panel class."""

    def test_panel_creation(self):
        """Test basic panel creation."""
        panel = s.Panel()
        assert panel.location is None
        assert panel.events == []
        assert panel.split_on_width is None

    def test_panel_with_location(self):
        """Test panel creation with location."""
        panel = s.Panel(location="public park, outdoor")
        assert panel.location == "public park, outdoor"

    def test_panel_bake(self):
        """Test panel baking combines events and location."""
        panel = s.Panel(location="park")
        panel.events = [s.Event("walking, happy"), s.Event("sunny day")]
        characters = {}
        result = panel.bake(characters)
        assert "walking, happy" in result
        assert "sunny day" in result
        assert "park" in result

    def test_panel_get_dialog_empty(self):
        """Test get_dialog with no dialog events."""
        panel = s.Panel()
        panel.events = [s.Event("walking")]  # No character, so no dialog
        assert panel.get_dialog() is None

    def test_panel_get_dialog_with_dialog(self):
        """Test get_dialog with dialog events."""
        panel = s.Panel()
        panel.events = [s.Event("Hello!", "misty")]
        dialogs = panel.get_dialog()
        assert dialogs is not None
        assert len(dialogs) == 1


class TestPage:
    """Tests for the Page class."""

    def test_page_parse_simple(self):
        """Test parsing a simple page line."""
        page = s.Page.parse("-Page1")
        assert page is not None
        assert page.name == "Page1"
        assert page.panel_min_percent is None
        assert page.mode == "separate"

    def test_page_parse_with_min(self):
        """Test parsing a page line with min parameter."""
        page = s.Page.parse("-Page1(min: (0.3, 0.3))")
        assert page is not None
        assert page.name == "Page1"
        assert page.panel_min_percent == (0.3, 0.3)

    def test_page_parse_with_mode(self):
        """Test parsing a page line with mode parameter."""
        page = s.Page.parse("-Page1(mode: controlnet)")
        assert page is not None
        assert page.name == "Page1"
        assert page.mode == "controlnet"

    def test_page_parse_with_multiple_params(self):
        """Test parsing a page line with multiple parameters."""
        page = s.Page.parse("-Page1(min: (0.3, 0.3) | mode: controlnet)")
        assert page is not None
        assert page.name == "Page1"
        assert page.panel_min_percent == (0.3, 0.3)
        assert page.mode == "controlnet"

    def test_page_get_splits(self):
        """Test get_splits returns correct split info."""
        page = s.Page("TestPage")
        page.panels = [
            s.Panel(split_on_width=True),
            s.Panel(split_on_width=False),
            s.Panel(split_on_width=None),
        ]
        splits = page.get_splits()
        assert splits == [False, None, None]


class TestScript:
    """Tests for the script parsing function."""

    def test_script_empty(self):
        """Test parsing an empty script."""
        result = s.script("")
        assert result == []

    def test_script_single_page(self):
        """Test parsing a script with a single page."""
        script_text = """-Page1

location: park

[misty] walking, happy
"Hello!"

"""
        result = s.script(script_text)
        assert len(result) == 1
        assert result[0].name == "Page1"
        assert len(result[0].panels) == 1
        assert result[0].panels[0].location == "park"

    def test_script_multiple_panels(self):
        """Test parsing a script with multiple panels."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"

[misty] running
"Bye!"

"""
        result = s.script(script_text)
        assert len(result) == 1
        assert len(result[0].panels) == 2

    def test_script_location_inheritance(self):
        """Test that location is inherited across panels."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"

[misty] running
"Bye!"

"""
        result = s.script(script_text)
        assert result[0].panels[0].location == "park"
        assert result[0].panels[1].location == "park"

    def test_script_location_change(self):
        """Test that location can be changed for panels."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"

location: indoor

[misty] sitting
"Hello!"

"""
        result = s.script(script_text)
        assert result[0].panels[0].location == "park"
        assert result[0].panels[1].location == "indoor"

    def test_script_split_directive(self):
        """Test parsing split directives."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"

split: h

[misty] running
"Bye!"

"""
        result = s.script(script_text)
        assert result[0].panels[0].split_on_width is None
        assert result[0].panels[1].split_on_width is True

    def test_script_comments(self):
        """Test that comments are ignored."""
        script_text = """-Page1

# This is a comment
location: park

[misty] walking
"Hi!"

"""
        result = s.script(script_text)
        assert len(result) == 1
        assert len(result[0].panels) == 1

    def test_script_multiple_pages(self):
        """Test parsing a script with multiple pages."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"

-Page2

location: indoor

[misty] sitting
"Hello!"

"""
        result = s.script(script_text)
        assert len(result) == 2
        assert result[0].name == "Page1"
        assert result[1].name == "Page2"

    def test_script_character_tracking(self):
        """Test that character is tracked across dialog."""
        script_text = """-Page1

location: park

[misty] walking
"Hi!"
"How are you?"

"""
        result = s.script(script_text)
        panel = result[0].panels[0]
        # Both dialogs should be attributed to misty
        assert len(panel.events) == 3  # scene description + 2 dialogs
        assert panel.events[1].character.name == "misty"
        assert panel.events[2].character.name == "misty"
