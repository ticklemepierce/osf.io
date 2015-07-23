import json
from nose.tools import *
from tests.base import OsfTestCase

from modularodm import Q
from website.models import Node
from tests.factories import NodeFactory
from scripts.migration.migrate_registered_meta import main as do_migration
from scripts.migration.migrate_registered_meta import IMMUTABLE_KEYS


class TestMigrateSchemas(OsfTestCase):
    def setUp(self):
        super(TestMigrateSchemas, self).setUp()

        self.reg_meta1 = json.dumps({
            'Open-Ended_Registration': {
                "registrationChoice": "immediate",
                "embargoEndDate":"Thu%2C 02 Jul 2015 00%3A08%3A22 GMT",
                "summary": "this is the most basic schema that we have"
            }
        })

        self.reg1 = NodeFactory(is_registration=True, registered_meta=self.reg_meta1, fits_prereg_schema=False)

        self.reg_meta2 = json.dumps({
            'V serious Registration': {
                "embargoEndDate": "Thu%2C 02 Jul 2015 00%3A08%3A22 GMT",
                "item1": "the nature",
                "item10": "yes",
                "item11": "asfd",
                "item12": "fasfsdf",
                "item13": "has anyone",
                "item14": "even been so",
                "item15": "far as",
                "item16": "decided to use",
                "item17": "Close",
                "item18": "Exact",
                "item19": "Exact",
                "item2":  "of the ",
                "item22": "Different",
                "item23": "Different",
                "item24": " even go want",
                "item25": " to do look more like%3F",
                "item26": "You%27ve got to be kidding me.",
                "item27": "I%27ve been further even more decided to use even go need to do look more as anyone can. C",
                "item28": "an you really be far even as decided half as much to use go wish for that%3F",
                "item3": "effect",
                "item4": "is so",
                "item5": "huge",
                "item6": "i need to see",
                "item7": "these ",
                "item8": "answers",
                "item9": "wat",
                "registrationChoice": "immediate"}
        })

        self.reg2 = NodeFactory(is_registration=True, registered_meta=self.reg_meta2, fits_prereg_schema=False)

    def test_migrate_json_schemas(self):
        do_migration(dry_run=False)
        migrated_nodes = Node.find(
            Q('is_registration', 'eq', True)
        )

        for node in migrated_nodes:
            assert_equal(node.fits_prereg_schema, True)
            registrations = node.registered_meta
            for name, data in registrations.iteritems():
                assert_in('embargoEndDate', data)
                assert_equal(data['embargoEndDate'], u'Thu%2C 02 Jul 2015 00%3A08%3A22 GMT')
                assert_in('registrationChoice', data)
                assert_equal(data['registrationChoice'], u'immediate')
                for item in data:
                    assert_not_in(item, IMMUTABLE_KEYS)
                    assert_not_equal(item, None)
                    if item != 'embargoEndDate' and item != 'registrationChoice':
                        assert_in('comments', data[item])
                        assert_not_equal(data[item]['comments'],u'Thu%2C 02 Jul 2015 13%3A34%3A27 GMT' )
                        assert_not_equal(data[item]['comments'],u'immediate' )
                        assert_in('value', data[item])
                        assert_not_equal(data[item]['value'], u'Thu%2C 02 Jul 2015 13%3A34%3A27 GMT' )
                        assert_not_equal(data[item]['value'], u'immediate' )
