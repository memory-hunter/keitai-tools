# Author: usernameak | /bin/cat

from construct import *
import construct
import os
import itertools
import sys
import scsu

checked_uid_struct = Struct(
    "uid" / Array(3, Int32ul),
    "checksum" / Int32ul
)

store_header_struct = Struct(
    "iBackup" / Int32ul,
    "iHandle" / Int32sl,
    "iRef" / Int32sl,
    "iCrc" / Int16ul,
)

toc_header_struct = Struct(
    "primary" / Int32ul,
    "avail" / Int32sl,
    "count" / Int32ul
)

toc_delta_header_struct = Struct(
    "tocoff" / Int32ul,
    "iMagic" / Int16ul,
    "n" / Int8ul
)

toc_entry_struct = Struct(
    "handle" / Int8ul,
    "ref" / Int32ul
)

toc_delta_entry_struct = Struct(
    "handle" / Int32ul,
    "ref" / Int32ul
)

class TCardinalityImpl(Construct):
    def _parse(self, stream, context, path):
        n = stream_read(stream, 1, path)[0]
        if (n & 0x1) == 0:
            return n >> 1
        elif (n & 0x2) == 0:
            n |= stream_read(stream, 1, path)[0] << 8
            return n >> 2
        elif (n & 0x4) == 0:
            arr = stream_read(stream, 3, path)
            n |= arr[0] << 8
            n |= arr[1] << 16
            n |= arr[2] << 24
            return n >> 3
        else:
            raise ValueError("invalid TCardinality value")

    def _build(self, obj, stream, context, path):
        if not isinstance(obj, int):
            raise IntegerError(f"value {obj} is not an integer", path=path)
        if obj < 0:
            raise IntegerError(f"TCardinality cannot build from negative number {obj}", path=path)
        n = obj
        if n < 0x80:
            n <<= 1
            stream_write(stream, bytes([n]), 1, path)
        elif n < 0x4000:
            n <<= 2
            stream_write(stream, bytes([n & 0xFF, (n >> 8) & 0xFF]), 2, path)
        elif n < 0x20000000:
            n <<= 3
            stream_write(stream, bytes([n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF, (n >> 24) & 0xFF]), 4, path)
        else:
            raise IntegerError(f"value {obj} is out of range for TCardinality", path=path)
        return obj

TCardinality = TCardinalityImpl()

class StringSizeAdapter(Adapter):
    def _decode(self, obj, context, path):
        return obj // 2

    def _encode(self, obj, context, path):
        return obj * 2

TDbName = PascalString(StringSizeAdapter(TCardinality), "SCSU")

class ReadBitSequence(Construct):
    def _parse(self, stream, context, path):
        cxroot = context._root

        if '_read_bit_entry' not in cxroot:
            cxroot['_read_bit_entry'] = 0
        
        cxroot['_read_bit_entry'] >>= 1
        if (cxroot['_read_bit_entry'] & 0x1000000) == 0:
            cxroot['_read_bit_entry'] = stream_read(stream, 1, path)[0] | 0xFF000000

        return cxroot['_read_bit_entry'] & 1

    def _build(self, obj, stream, context, path):
        raise ValueError("_build not supported for ReadBitSequence")

column_schema_struct = Struct(
    "name" / TDbName,
    "type" / Int8ul,
    "attributes" / Int8ul,
    "maxLength" / If((this.type >= 11) & (this.type <= 13), Int8ul)
)

key_col_def_struct = Struct(
    "name" / TDbName,
    "iLength" / Int8ul,
    "iOrder" / Int8ul
)

index_def_struct = Struct(
    "name" / TDbName,
    "comparison" / Int8ul,
    "isUnique" / Int8ul,
    "keys" / PrefixedArray(TCardinality, key_col_def_struct),
    "iTokenId" / Int32ul,
)

table_schema_struct = Struct(
    "name" / TDbName,
    "columns" / PrefixedArray(TCardinality, column_schema_struct),
    "cluster" / TCardinality,
    "iTokenId" / Int32ul,
    "indexes" / PrefixedArray(TCardinality, index_def_struct)
)

db_schema_struct = Struct(
    "uid" / Int32ul,
    "iVersion" / Int8ul,
    "iToken" / Int32ul,
    "tables" / PrefixedArray(TCardinality, table_schema_struct)
)

ATTRIB_NOT_NULL = 1

class StoreToc:
    def __init__(self):
        self.primary = 0
        self.entries = []

    def parse(self, data, offset):
        toc_header = toc_header_struct.parse(data[offset-12:offset])
        if toc_header.primary & 0x80000000:
            toc_delta_header = toc_delta_header_struct.parse(data[offset:offset+7])

            self.parse(data, toc_delta_header.tocoff)

            toc_delta_entries = Array(toc_delta_header.n, toc_delta_entry_struct).parse(data[offset+7:offset+7+(toc_delta_header.n*8)])

            self.entries.extend(itertools.repeat(-1, toc_header.count - len(self.entries)))
            for entry in toc_delta_entries:
                self.entries[(entry.handle & 0xFFFFFF) - 1] = entry.ref
        else:
            toc_entries = Array(toc_header.count, toc_entry_struct).parse(data[offset:offset+(toc_header.count*5)])
            self.entries = [e.ref for e in toc_entries]

        self.primary = toc_header.primary & 0x7FFFFFFF

    def num_entries(self):
        return len(self.entries)

    def get_offset(self, handle):
        return self.entries[handle - 1]
    
table_token_struct = Struct(
    "iHead" / Int32ul, # head cluster ID
    "iNext" / Int32ul, # next record id?
    "iCount" / TCardinality,
    "iAutoIncrement" / Int32ul
)

cluster_struct = Struct(
    "iNext" / Int32ul, # next record id?
    "iMembership" / BitsSwapped(Bitwise(Array(16, Bit))),
    "sizes" / Array(16, If(lambda this: this.iMembership[this._index], TCardinality)),
    "data" / Array(16, If(lambda this: this.sizes[this._index] is not None, Bytes(lambda this: this.sizes[this._index])))
)