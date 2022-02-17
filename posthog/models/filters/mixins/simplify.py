from typing import TYPE_CHECKING, Any, Dict, List, Literal, TypeVar, cast

from posthog.models.property import GroupTypeIndex

if TYPE_CHECKING:  # Avoid circular import
    from posthog.models import Property, Team
    from posthog.models.property import PropertyGroup

T = TypeVar("T")


class SimplifyFilterMixin:
    # :KLUDGE: A lot of this logic ignores typing since generics w/ mixins are hard to get working properly
    def simplify(self: T, team: "Team", **kwargs) -> T:
        """
        Expands this filter to not refer to external resources of the team.

        Actions taken:
        - if filter.filter_test_accounts, adds property filters to `filter.properties`
        - if aggregating by groups, adds property filter to remove blank groups
        - for cohort properties, replaces them with more concrete lookups or with cohort conditions
        """

        if self._data.get("is_simplified"):  # type: ignore
            return self

        # :TRICKY: Make a copy to avoid caching issues
        result: Any = self.with_data({"is_simplified": True})  # type: ignore
        new_group_props = []

        if getattr(result, "filter_test_accounts", False):
            result = result.with_data({"filter_test_accounts": False,})
            new_group_props += team.test_account_filters

        updated_entities = {}
        if hasattr(result, "entities_to_dict"):
            for entity_type, entities in result.entities_to_dict().items():
                updated_entities[entity_type] = [self._simplify_entity(team, entity_type, entity, **kwargs) for entity in entities]  # type: ignore

        prop_group = self._simplify_property_group(team, result.property_groups, **kwargs).to_dict()  # type: ignore

        if getattr(result, "aggregation_group_type_index", None) is not None:
            new_group_props.append(self._group_set_property(cast(int, result.aggregation_group_type_index)).to_dict())  # type: ignore

        if new_group_props:
            new_group_props = [prop for prop in new_group_props]
            new_group = {"type": "AND", "values": new_group_props}
            prop_group = {"type": "AND", "values": [new_group, prop_group]} if prop_group else new_group

        return result.with_data({**updated_entities, "properties": prop_group})

    def _simplify_entity(
        self, team: "Team", entity_type: Literal["events", "actions", "exclusions"], entity_params: Dict, **kwargs
    ) -> Dict:
        from posthog.models.entity import Entity, ExclusionEntity

        EntityClass = ExclusionEntity if entity_type == "exclusions" else Entity

        entity = EntityClass(entity_params)
        properties = self._simplify_properties(team, entity.properties, **kwargs)
        if entity.math == "unique_group":
            properties.append(self._group_set_property(cast(GroupTypeIndex, entity.math_group_type_index)))

        return EntityClass({**entity_params, "properties": properties}).to_dict()

    def _simplify_properties(self, team: "Team", properties: List["Property"], **kwargs) -> List["Property"]:
        simplified_properties = []
        for prop in properties:
            simplified_properties.extend(self._simplify_property(team, prop, **kwargs))
        return simplified_properties

    def _simplify_property_group(self, team: "Team", prop_group: "PropertyGroup", **kwargs) -> "PropertyGroup":
        from posthog.models.property import Property, PropertyGroup

        new_groups = []
        for group in prop_group.values:
            if isinstance(group, PropertyGroup):
                new_groups.append(self._simplify_property_group(team, group))
            elif isinstance(group, Property):
                new_groups.extend(self._simplify_property(team, group))  # type: ignore

        prop_group.values = new_groups
        return prop_group

    def _simplify_property(self, team: "Team", property: "Property", **kwargs) -> List["Property"]:
        if property.type == "cohort":
            from ee.clickhouse.models.cohort import simplified_cohort_filter_properties
            from posthog.models import Cohort

            try:
                cohort = Cohort.objects.get(pk=property.value, team_id=team.pk)
            except Cohort.DoesNotExist:
                # :TODO: Handle non-existing resource in-query instead
                return [property]

            return simplified_cohort_filter_properties(cohort, team)

        return [property]

    def _group_set_property(self, group_type_index: GroupTypeIndex) -> "Property":
        from posthog.models.property import Property

        return Property(key=f"$group_{group_type_index}", value="", operator="is_not",)

    @property
    def is_simplified(self) -> bool:
        return self._data.get("is_simplified", False)  # type: ignore
