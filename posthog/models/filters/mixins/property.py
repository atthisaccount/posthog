import json
from typing import Any, Dict, Iterator, List, Optional, Union, cast

from rest_framework.exceptions import ValidationError

from posthog.constants import PROPERTIES, PROPERTY_GROUPS, PropertyOperatorType
from posthog.models.filters.mixins.base import BaseParamMixin
from posthog.models.filters.mixins.utils import cached_property, include_dict
from posthog.models.property import Property, PropertyGroup


class PropertyMixin(BaseParamMixin):
    @cached_property
    def properties(self) -> List[Property]:
        _props = self._data.get(PROPERTIES)

        if isinstance(_props, str):
            try:
                loaded_props = json.loads(_props)
            except json.decoder.JSONDecodeError:
                raise ValidationError("Properties are unparsable!")
        else:
            loaded_props = _props

        # if grouped properties
        if isinstance(loaded_props, dict) and "type" in loaded_props and "groups" in loaded_props:
            # property_groups is main function from now on
            # TODO: this function will go away at end of migration
            return []
        else:
            # old style dict properties or a list of properties
            return self._parse_properties(loaded_props)

    @cached_property
    def property_groups(self) -> PropertyGroup:
        _props = self._data.get(PROPERTIES)

        if isinstance(_props, str):
            try:
                loaded_props = json.loads(_props)
            except json.decoder.JSONDecodeError:
                raise ValidationError("Properties are unparsable!")
        else:
            loaded_props = _props

        # if grouped properties
        if isinstance(loaded_props, dict) and "type" in loaded_props and "groups" in loaded_props:
            try:
                return self._parse_property_group(loaded_props)
            except ValidationError as e:
                raise e
            except ValueError as e:
                raise ValidationError(f"PropertyGroup is unparsable: {e}")

        # old properties
        return PropertyGroup(type=PropertyOperatorType.AND, groups=self.properties)

    @cached_property
    def property_groups_flat(self) -> List[Property]:
        return list(self._property_groups_flat(self.property_groups))

    def _property_groups_flat(self, prop_group: PropertyGroup):
        for _group in prop_group.groups:
            if isinstance(_group, PropertyGroup):
                yield from self._property_groups_flat(_group)
            else:
                yield _group

    def _parse_properties(self, properties: Optional[Any]) -> List[Property]:
        if isinstance(properties, list):
            _properties = []
            for prop_params in properties:
                if isinstance(prop_params, Property):
                    _properties.append(prop_params)
                else:
                    try:
                        new_prop = Property(**prop_params)
                        _properties.append(new_prop)
                    except:
                        continue
            return _properties
        if not properties:
            return []

        # old style dict properties
        ret = []
        for key, value in properties.items():
            key_split = key.split("__")
            ret.append(
                Property(
                    key=key_split[0], value=value, operator=key_split[1] if len(key_split) > 1 else None, type="event",
                )
            )
        return ret

    def _parse_property_group(self, group: Optional[Dict]) -> PropertyGroup:
        if group and "type" in group and "groups" in group:
            return PropertyGroup(
                PropertyOperatorType(group["type"].upper()), self._parse_property_group_list(group["groups"])
            )

        return PropertyGroup(PropertyOperatorType.AND, cast(List[Property], []))

    def _parse_property_group_list(self, prop_list: Optional[List]) -> Union[List[Property], List[PropertyGroup]]:
        if not prop_list:
            # empty prop list
            return cast(List[Property], [])
        has_property_groups = False
        has_simple_properties = False
        for prop in prop_list:
            if "type" in prop and "groups" in prop:
                has_property_groups = True
            else:
                has_simple_properties = True

        if has_simple_properties and has_property_groups:
            raise ValidationError("Property list cannot contain both PropertyGroup and Property objects")

        if has_property_groups:
            return [self._parse_property_group(group) for group in prop_list]
        else:
            return self._parse_properties(prop_list)

    @include_dict
    def properties_to_dict(self):
        return (
            {PROPERTIES: self.property_groups.to_dict()} if self.property_groups and self.property_groups.groups else {}
        )
