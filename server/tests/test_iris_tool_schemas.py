from __future__ import annotations

import asyncio
import unittest

from support import ProjectTestCase

from trellis_mcp.server import create_mcp


class IrisToolSchemaTests(ProjectTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tools = {tool.name: tool for tool in asyncio.run(create_mcp("iris").list_tools())}

    def test_every_exposed_field_has_a_description(self) -> None:
        for tool_name, tool in self.tools.items():
            with self.subTest(tool=tool_name):
                self.assertTrue(tool.description)
                for field_name, field_schema in tool.parameters.get("properties", {}).items():
                    with self.subTest(tool=tool_name, field=field_name):
                        self.assertTrue(field_schema.get("description"))

    def test_fixed_modes_lenses_and_handoff_status_expose_fixed_values(self) -> None:
        writer = self.tools["create_spec_writer_assignment"].parameters["properties"]
        self.assertEqual(writer["mode"]["enum"], ["master", "single"])
        self.assertIn("mode", self.tools["create_spec_writer_assignment"].parameters["required"])

        advisor = self.tools["create_advisor_assignment"].parameters["properties"]
        self.assertEqual(advisor["mode"]["enum"], ["independent_decision", "reconciliation"])
        self.assertEqual(
            advisor["primary_lens"]["enum"],
            [
                "security_authority",
                "runtime_implementability",
                "proportionality",
                "cross_lens_reconciliation",
            ],
        )
        reviewer = self.tools["create_spec_reviewer_assignment"].parameters["properties"]
        self.assertEqual(
            reviewer["lens"]["enum"],
            ["general", "product", "risk", "overengineering", "design_conformance"],
        )
        self.assertIn("mode", self.tools["create_advisor_assignment"].parameters["required"])
        self.assertIn("decision_question", self.tools["create_advisor_assignment"].parameters["required"])

        handoff = self.tools["handoff_to_ben"].parameters["properties"]
        self.assertEqual(handoff["status"]["const"], "ready_for_ben")
        self.assertEqual(handoff["status"]["default"], "ready_for_ben")
        self.assertIn("After review and scope approval", self.tools["handoff_to_ben"].description)

    def test_round_constraints_match_transport_behavior(self) -> None:
        creation_tools = (
            "create_scout_assignment",
            "create_research_assignment",
            "create_advisor_assignment",
            "create_spec_writer_assignment",
            "create_spec_reviewer_assignment",
        )
        for tool_name in creation_tools:
            with self.subTest(tool=tool_name):
                round_schema = self.tools[tool_name].parameters["properties"]["round"]
                self.assertEqual(round_schema["default"], 1)
                self.assertEqual(round_schema["minimum"], 1)

        lookup_tools = (
            "get_scout_assignment",
            "get_research_assignment",
            "get_advisor_assignment",
            "get_spec_writer_assignment",
            "get_spec_reviewer_assignment",
        )
        for tool_name in lookup_tools:
            with self.subTest(tool=tool_name):
                round_schema = self.tools[tool_name].parameters["properties"]["round"]
                self.assertEqual(round_schema["default"], 0)
                self.assertEqual(round_schema["minimum"], 0)
                self.assertIn("latest", round_schema["description"])

    def test_ids_and_ranges_expose_existing_validation_constraints(self) -> None:
        scout = self.tools["create_scout_assignment"].parameters["properties"]
        self.assertEqual(scout["specflow_id"]["pattern"], r"^[a-z0-9][a-z0-9-]{1,120}$")
        self.assertEqual(scout["task_id"]["pattern"], r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")

        read_chats = self.tools["read_chats"].parameters["properties"]
        self.assertEqual(read_chats["count"]["minimum"], 1)
        self.assertEqual(read_chats["start"]["anyOf"][0]["minimum"], 1)
        self.assertEqual(read_chats["end"]["anyOf"][0]["minimum"], 1)

        read_assignment_log = self.tools["read_assignment_log"].parameters["properties"]
        self.assertEqual(read_assignment_log["count"]["minimum"], 1)
        self.assertEqual(read_assignment_log["start"]["anyOf"][0]["minimum"], 1)
        self.assertEqual(read_assignment_log["end"]["anyOf"][0]["minimum"], 1)

    def test_assignment_log_tools_are_provenance_only(self) -> None:
        append = self.tools["append_assignment_log"]
        properties = append.parameters["properties"]

        self.assertIn("provenance", append.description.lower())
        self.assertIn("does not imply product authority", properties["author"]["description"])
        self.assertIn("Do not copy product/spec content", properties["message"]["description"])

    def test_flexible_fields_are_described_without_false_enums(self) -> None:
        scout_lens = self.tools["create_scout_assignment"].parameters["properties"]["lens"]
        advisor_focus = self.tools["create_advisor_assignment"].parameters["properties"]["focus"]
        review_focus = self.tools["create_spec_reviewer_assignment"].parameters["properties"]["focus"]

        self.assertNotIn("enum", scout_lens)
        self.assertIn("bounded perspective", scout_lens["description"])
        self.assertNotIn("enum", advisor_focus)
        self.assertIn("does not limit", advisor_focus["description"])
        self.assertNotIn("enum", review_focus)
        self.assertIn("assigned review lens", review_focus["description"])

    def test_advisor_assignment_exposes_neutral_decision_contract(self) -> None:
        schema = self.tools["create_advisor_assignment"].parameters
        properties = schema["properties"]

        self.assertIn("neutral", properties["decision_question"]["description"].lower())
        self.assertIn("user-approved outcome", properties["approved_outcome"]["description"].lower())
        self.assertIn("user-approved", properties["user_approved_constraints"]["description"].lower())
        self.assertIn("without declaring one authoritative", properties["options_visible"]["description"])
        self.assertIn("primary evidence", properties["claims_requiring_verification"]["description"])
        self.assertIn("authority boundary", properties["changed_boundaries_requiring_closure"]["description"])
        self.assertIn("complete cross-lens", properties["primary_lens"]["description"])

        for field in (
            "approved_outcome",
            "user_approved_constraints",
            "options_visible",
            "claims_requiring_verification",
            "changed_boundaries_requiring_closure",
            "primary_lens",
            "focus",
        ):
            self.assertIn(field, schema["required"])
        self.assertNotIn("outcome_summary", properties)
        self.assertNotIn("direct_constraints", properties)

    def test_research_questions_expose_bounded_assignment_contract(self) -> None:
        schema = self.tools["create_research_assignment"].parameters
        properties = schema["properties"]
        research_questions = properties["research_questions"]

        self.assertIn("at most three", research_questions["description"].lower())
        self.assertIn("exclude specification", research_questions["description"])
        self.assertIn("one route", properties["routing_decision"]["description"])
        self.assertIn("stop", properties["stopping_condition"]["description"])
        self.assertIn("routing_decision", schema["required"])
        self.assertIn("research_questions", schema["required"])
        self.assertIn("stopping_condition", schema["required"])

    def test_subagent_slot_schema_exposes_stable_identity(self) -> None:
        register = self.tools["register_subagent"].parameters["properties"]
        self.assertEqual(register["orchestrator"]["enum"], ["ben", "sunny", "iris"])
        self.assertEqual(register["role"]["pattern"], r"^[A-Za-z][A-Za-z0-9_-]{0,80}$")
        self.assertEqual(register["nickname"]["anyOf"][0]["maxLength"], 100)
        self.assertIn("parallel agents", register["nickname"]["description"])


if __name__ == "__main__":
    unittest.main()
