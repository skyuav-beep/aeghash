from pathlib import Path

import pytest

STORYBOOK_PREVIEW = Path("examples/frontend-storybook/.storybook/preview.ts")
STORYBOOK_MAIN = Path("examples/frontend-storybook/.storybook/main.ts")
BUTTON_COMPONENT = Path("examples/frontend-storybook/src/components/Button.tsx")
ADMIN_STORY_FILES = [
    Path("examples/frontend-storybook/src/stories/admin/ui-kit/Button.stories.tsx"),
    Path("examples/frontend-storybook/src/stories/admin/ui-kit/Input.stories.tsx"),
    Path("examples/frontend-storybook/src/stories/admin/ui-kit/Card.stories.tsx"),
]


@pytest.mark.a11y
def test_storybook_a11y_addon_enabled() -> None:
    content = STORYBOOK_PREVIEW.read_text(encoding="utf-8")
    assert "a11y" in content, "Storybook preview must enable the a11y addon for automated checks."


@pytest.mark.a11y
def test_storybook_viewport_addon_enabled() -> None:
    main_config = STORYBOOK_MAIN.read_text(encoding="utf-8")
    assert (
        "@storybook/addon-viewport" in main_config
    ), "Viewport addon should be enabled for breakpoint coverage."


@pytest.mark.a11y
@pytest.mark.parametrize("story_path", ADMIN_STORY_FILES)
def test_admin_ui_kit_story_registered(story_path: Path) -> None:
    assert story_path.exists(), f"{story_path} is missing."
    text = story_path.read_text(encoding="utf-8")
    assert 'title: "Admin/UI Kit/' in text, "Story should be grouped under Admin/UI Kit."


@pytest.mark.a11y
def test_button_component_exposes_loading_semantics() -> None:
    button_code = BUTTON_COMPONENT.read_text(encoding="utf-8")
    assert "aria-busy" in button_code, "Loading 상태는 aria-busy 속성을 통해 노출되어야 합니다."
    assert "disabled={isDisabled}" in button_code, "Loading 상태는 disabled와 함께 적용되어야 합니다."
