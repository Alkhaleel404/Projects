import unittest

from preparedness import (
    CHECKLIST,
    create_checklist_text,
    select_checklist_items,
)


class PreparednessTests(unittest.TestCase):
    def test_custom_checklist_excludes_unselected_topics(self) -> None:
        items = select_checklist_items(
            include_pets=False,
            include_documents=False,
            include_travel=False,
        )
        text = create_checklist_text(set(), items)
        self.assertNotIn("Plan for pets", text)
        self.assertNotIn("important documents", text)
        self.assertNotIn("Check official alerts before traveling", text)
        self.assertIn("Never enter floodwater", text)

    def test_download_text_marks_completed_items(self) -> None:
        text = create_checklist_text({"water"})
        self.assertIn("[x] Stay out of floodwater", text)
        self.assertIn("[ ] Turn on trusted weather and emergency alerts", text)

    def test_unknown_completion_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_checklist_text({"unexpected"})

    def test_default_checklist_has_all_phases(self) -> None:
        text = create_checklist_text(set())
        for phase in ("Before heavy rain", "During heavy rain", "After heavy rain"):
            self.assertIn(phase, text)
        self.assertEqual(len(CHECKLIST), 9)


if __name__ == "__main__":
    unittest.main()
