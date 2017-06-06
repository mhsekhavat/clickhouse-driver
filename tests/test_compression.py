from datetime import date, datetime
from src.compression import get_compressor_cls

from .testcase import BaseTestCase, file_config
from src import errors
from src.client import Client


class BaseCompressionTestCase(BaseTestCase):
    compression = False
    supported_compressions = file_config.get('db', 'compression').split(',')

    @classmethod
    def create_client(cls):
        return Client(cls.host, cls.port, cls.database, cls.user, cls.password,
                      compression=cls.compression)

    def setUp(self):
        supported = (
            self.compression is False or
            self.compression in self.supported_compressions
        )

        if not supported:
            self.skipTest(
                'Compression {} is not supported'.format(self.compression)
            )

    def run_simple(self):
        with self.create_table('a Date, b DateTime'):
            data = [(date(2012, 10, 25), datetime(2012, 10, 25, 14, 7, 19))]
            self.client.execute(
                'INSERT INTO test (a, b) VALUES', data
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, '2012-10-25\t2012-10-25 14:07:19\n')

            inserted = self.client.execute(query)
            self.assertEqual(inserted, data)

    def test(self):
        if self.compression is False:
            return

        self.run_simple()


class QuickLZReadWriteTestCase(BaseCompressionTestCase):
    compression = 'quicklz'


class LZ4ReadWriteTestCase(BaseCompressionTestCase):
    compression = 'lz4'


class LZ4HCReadWriteTestCase(BaseCompressionTestCase):
    compression = 'lz4hc'


class ZSTDReadWriteTestCase(BaseCompressionTestCase):
    compression = 'zstd'


class UnknownCompressionTestCase(BaseCompressionTestCase):
    def test(self):
        with self.assertRaises(errors.UnknownCompressionMethod) as e:
            get_compressor_cls('hello')

        self.assertEqual(
            e.exception.code, errors.ErrorCodes.UNKNOWN_COMPRESSION_METHOD
        )


class ReadByBlocksTestCase(BaseCompressionTestCase):
    compression = 'lz4'

    def test(self):
        with self.create_table('a Int32'):
            data = [(x % 200, ) for x in range(1000000)]

            self.client.execute(
                'INSERT INTO test (a) VALUES', data
            )

            query = 'SELECT * FROM test'

            inserted = self.client.execute(query)
            self.assertEqual(inserted, data)
