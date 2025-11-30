"""Tests for the panel_generator module."""
import pytest
from unittest.mock import patch, MagicMock
from castadi import panel_generator as pg


class TestSplitRec:
    """Tests for the split_rec function."""

    def test_split_rec_too_small(self):
        """Test that small rectangles are not split."""
        rec = (0, 0, 100, 100)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size)
        assert result == [rec]

    def test_split_rec_width_only(self):
        """Test splitting when only width allows split.
        
        Note: Due to randomness in split behavior, we seed the random
        generator for deterministic results.
        """
        import random
        random.seed(0)
        rec = (0, 0, 300, 100)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size)
        # Should produce 2 panels
        assert len(result) == 2
        # Height should be preserved
        assert result[0][3] == 100
        assert result[1][3] == 100

    def test_split_rec_height_only(self):
        """Test splitting when only height allows split.
        
        Note: Due to randomness in split direction, this test uses
        a seed to ensure deterministic behavior.
        """
        import random
        random.seed(42)
        rec = (0, 0, 100, 300)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size)
        # Should produce 2 panels
        assert len(result) == 2
        # Both panels should have the same width as original
        assert result[0][2] == 100
        assert result[1][2] == 100

    def test_split_rec_forced_width_split(self):
        """Test forced width split."""
        rec = (0, 0, 300, 300)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size, split_on_width=True)
        # Should split on height (split_on_width=True means horizontal division)
        assert len(result) == 2
        total_height = result[0][3] + result[1][3]
        assert total_height == 300
        assert result[0][2] == 300
        assert result[1][2] == 300

    def test_split_rec_forced_height_split(self):
        """Test forced height split."""
        rec = (0, 0, 300, 300)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size, split_on_width=False)
        # Should split on width (split_on_width=False means vertical division)
        assert len(result) == 2
        total_width = result[0][2] + result[1][2]
        assert total_width == 300
        assert result[0][3] == 300
        assert result[1][3] == 300

    def test_split_rec_preserves_position(self):
        """Test that split preserves rectangle position."""
        rec = (100, 200, 300, 300)
        min_size = (100, 100)
        result = pg.split_rec(rec, min_size, split_on_width=True)
        assert len(result) == 2
        # First rect should start at original position
        assert result[0][0] == 100
        assert result[0][1] == 200
        # Second rect should be positioned after first
        assert result[1][0] == 100
        assert result[1][1] == 200 + result[0][3]


class TestGetPanels:
    """Tests for the get_panels function."""

    def test_get_panels_single(self):
        """Test getting a single panel (no split needed)."""
        result = pg.get_panels(1, panels=[(0, 0, 1080, 1920)], min_size=(227, 225))
        assert len(result) == 1
        assert result[0] == (0, 0, 1080, 1920)

    def test_get_panels_two(self):
        """Test getting two panels."""
        result = pg.get_panels(2, panels=[(0, 0, 1080, 1920)], min_size=(227, 225))
        assert len(result) == 2
        # All panels should have valid dimensions
        for panel in result:
            x, y, width, height = panel
            assert width >= 227
            assert height >= 225
            assert x >= 0
            assert y >= 0

    def test_get_panels_three(self):
        """Test getting three panels."""
        result = pg.get_panels(3, panels=[(0, 0, 1080, 1920)], min_size=(227, 225))
        assert len(result) == 3
        for panel in result:
            x, y, width, height = panel
            assert width >= 227
            assert height >= 225

    def test_get_panels_with_splits(self):
        """Test getting panels with predefined splits."""
        # Two panels with horizontal split first
        result = pg.get_panels(2, panels=[(0, 0, 1080, 1920)], 
                               min_size=(227, 225), 
                               split_on_width=[True])
        assert len(result) == 2
        # With horizontal split, width should be preserved for both
        assert result[0][2] == 1080
        assert result[1][2] == 1080

    def test_get_panels_returns_sorted(self):
        """Test that panels are returned sorted by position."""
        import random
        random.seed(42)
        result = pg.get_panels(3, panels=[(0, 0, 1080, 1920)], min_size=(227, 225))
        # Should be sorted by (x, y)
        positions = [(p[0], p[1]) for p in result]
        assert positions == sorted(positions)


class TestDrawRectangles:
    """Tests for the draw_rectangles function."""

    def test_draw_rectangles_no_images(self):
        """Test drawing rectangles without images."""
        locations = [(0, 0, 540, 960)]
        canvas = pg.draw_rectangles(
            None, 
            locations, 
            None,
            canvas_size=(540, 960)
        )
        assert canvas is not None
        assert canvas.size == (540, 960)

    def test_draw_rectangles_reverse_mode(self):
        """Test drawing rectangles in reverse mode."""
        locations = [(0, 0, 540, 960)]
        canvas = pg.draw_rectangles(
            None, 
            locations, 
            None,
            reverse=True,
            canvas_size=(540, 960)
        )
        assert canvas is not None
        assert canvas.size == (540, 960)

    def test_draw_rectangles_with_bubbles(self):
        """Test drawing rectangles with speech bubbles.
        
        Note: This test is simplified due to font dependencies.
        Full bubble rendering requires a valid font file.
        """
        # Test basic canvas creation with bubble list
        # Bubble rendering requires font files which may not be available
        locations = [(0, 0, 540, 960)]
        
        # Without actual font, we can only test that the function handles
        # the case where bubbles is None gracefully
        canvas = pg.draw_rectangles(
            None, 
            locations, 
            None,  # No bubbles to avoid font dependency
            canvas_size=(540, 960),
        )
        assert canvas is not None

    def test_draw_rectangles_multiple_panels(self):
        """Test drawing multiple rectangles."""
        locations = [
            (0, 0, 540, 480),
            (0, 480, 540, 480),
        ]
        canvas = pg.draw_rectangles(
            None, 
            locations, 
            None,
            canvas_size=(540, 960)
        )
        assert canvas is not None
        assert canvas.size == (540, 960)
