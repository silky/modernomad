from graphene import AbstractType, Field, Node, List, Boolean
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from core.models import Location, Fee, LocationFee
from .resources import ResourceNode


class FeeNode(DjangoObjectType):
    class Meta:
        model = Fee
        interfaces = (Node, )


class LocationNode(DjangoObjectType):
    fees = List(lambda: FeeNode, paid_by_house=Boolean())
    resources = List(lambda: ResourceNode, has_future_capacity=Boolean())

    class Meta:
        model = Location
        interfaces = (Node, )
        filter_fields = ['slug']

    def resolve_fees(self, args, *_):
        query = Fee.objects.filter(locationfee__location=self)
        query = query.filter(**args)

        return query

    def resolve_resources(self, args, *_):
        if args.get('has_future_capacity', False):
            resources = self.rooms_with_future_capacity()
        else:
            resources = self.resources.all()
        return resources
            
        


class Query(AbstractType):
    all_locations = DjangoFilterConnectionField(LocationNode)
