from django.db import connection
from django.test import TestCase

from bitfield import BitHandler, Bit
from bitfield.tests import BitFieldTestModel

class BitHandlerTest(TestCase):
    def test_defaults(self):
        bithandler = BitHandler(0, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        # Default value of 0.
        self.assertEquals(int(bithandler), 0)
        # Test bit numbers.
        self.assertEquals(int(bithandler.FLAG_0.number), 0)
        self.assertEquals(int(bithandler.FLAG_1.number), 1)
        self.assertEquals(int(bithandler.FLAG_2.number), 2)
        self.assertEquals(int(bithandler.FLAG_3.number), 3)
        # Negative test non-existant key.
        self.assertRaises(AttributeError, lambda: bithandler.FLAG_4)
        # Test bool().
        self.assertEquals(bool(bithandler.FLAG_0), False)
        self.assertEquals(bool(bithandler.FLAG_1), False)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

    def test_nonzero_default(self):
        bithandler = BitHandler(1, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        self.assertEquals(bool(bithandler.FLAG_0), True)
        self.assertEquals(bool(bithandler.FLAG_1), False)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

        bithandler = BitHandler(2, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        self.assertEquals(bool(bithandler.FLAG_0), False)
        self.assertEquals(bool(bithandler.FLAG_1), True)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

        bithandler = BitHandler(3, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        self.assertEquals(bool(bithandler.FLAG_0), True)
        self.assertEquals(bool(bithandler.FLAG_1), True)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

        bithandler = BitHandler(4, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        self.assertEquals(bool(bithandler.FLAG_0), False)
        self.assertEquals(bool(bithandler.FLAG_1), False)
        self.assertEquals(bool(bithandler.FLAG_2), True)
        self.assertEquals(bool(bithandler.FLAG_3), False)

    def test_mutation(self):
        bithandler = BitHandler(0, ('FLAG_0', 'FLAG_1', 'FLAG_2', 'FLAG_3'))
        self.assertEquals(bool(bithandler.FLAG_0), False)
        self.assertEquals(bool(bithandler.FLAG_1), False)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

        bithandler = BitHandler(bithandler | 1, bithandler._keys)
        self.assertEquals(bool(bithandler.FLAG_0), True)
        self.assertEquals(bool(bithandler.FLAG_1), False)
        self.assertEquals(bool(bithandler.FLAG_2), False)
        self.assertEquals(bool(bithandler.FLAG_3), False)

        bithandler ^= 3
        self.assertEquals(int(bithandler), 2)

        self.assertEquals(bool(bithandler & 1), False)

class BitTest(TestCase):
    def test_int(self):
        bit = Bit(0, 1)
        self.assertEquals(int(bit), 1)
        self.assertEquals(bool(bit), True)
        self.assertFalse(not bit)

class BitFieldTest(TestCase):
    def test_basic(self):
        # Create instance and make sure flags are working properly.
        instance = BitFieldTestModel.objects.create(flags=1)
        self.assertTrue(instance.flags.FLAG_0)
        self.assertFalse(instance.flags.FLAG_1)
        self.assertFalse(instance.flags.FLAG_2)
        self.assertFalse(instance.flags.FLAG_3)

    def test_regression_1425(self):
        # Creating new instances shouldn't allow negative values.
        instance = BitFieldTestModel.objects.create(flags=-1)
        self.assertEqual(instance.flags._value, 15)
        self.assertTrue(instance.flags.FLAG_0)
        self.assertTrue(instance.flags.FLAG_1)
        self.assertTrue(instance.flags.FLAG_2)
        self.assertTrue(instance.flags.FLAG_3)

        cursor = connection.cursor()
        cursor.execute("INSERT INTO %s (flags) VALUES (-1)" % (BitFieldTestModel._meta.db_table,));
        # There should only be the one row we inserted through the cursor.
        instance = BitFieldTestModel.objects.get(flags=-1)
        self.assertTrue(instance.flags.FLAG_0)
        self.assertTrue(instance.flags.FLAG_1)
        self.assertTrue(instance.flags.FLAG_2)
        self.assertTrue(instance.flags.FLAG_3)
        instance.save()

        self.assertEqual(BitFieldTestModel.objects.filter(flags=15).count(), 2)
        self.assertEqual(BitFieldTestModel.objects.filter(flags__lt=0).count(), 0)

    def test_select(self):
        instance = BitFieldTestModel.objects.create(flags=3)
        self.assertTrue(BitFieldTestModel.objects.filter(flags=BitFieldTestModel.flags.FLAG_1).exists())
        self.assertTrue(BitFieldTestModel.objects.filter(flags=BitFieldTestModel.flags.FLAG_0).exists())
        self.assertFalse(BitFieldTestModel.objects.exclude(flags=BitFieldTestModel.flags.FLAG_0).exists())
        self.assertFalse(BitFieldTestModel.objects.exclude(flags=BitFieldTestModel.flags.FLAG_1).exists())

    def test_update(self):
        instance = BitFieldTestModel.objects.create(flags=0)
        self.assertFalse(instance.flags.FLAG_0)
        BitFieldTestModel.objects.filter(pk=instance.pk).update(flags=BitFieldTestModel.flags.FLAG_0)
        instance = BitFieldTestModel.objects.get(pk=instance.pk)
        self.assertTrue(instance.flags.FLAG_0)
        BitFieldTestModel.objects.filter(pk=instance.pk).update(flags=~BitFieldTestModel.flags.FLAG_0)
        instance = BitFieldTestModel.objects.get(pk=instance.pk)
        self.assertFalse(instance.flags.FLAG_0)
        self.assertFalse(BitFieldTestModel.objects.filter(flags=BitFieldTestModel.flags.FLAG_0).exists())

    def test_save(self):
        instance = BitFieldTestModel.objects.create(flags=BitFieldTestModel.flags.FLAG_0)
        self.assertTrue(BitFieldTestModel.objects.filter(flags=BitFieldTestModel.flags.FLAG_0).exists())