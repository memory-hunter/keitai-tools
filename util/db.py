# Author: usernameak | /bin/cat

from construct import *
import os
import itertools
import scsu
from util.constants import FJJAM_WANTED_COLS
from datetime import datetime, timedelta

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

def extract_jam_objects(fjjam_path: os.PathLike, verbose=False):
    # Author: usernameak | /bin/cat
    with open(fjjam_path, "rb") as f:
        checked_uid = checked_uid_struct.parse(f.read(16))
        store_header = store_header_struct.parse(f.read(16))

        if store_header.iBackup & 1:
            raise ValueError("ERROR: Store is dirty! Quitting processing.")

        data = bytearray()
        while True:
            buf = f.read(0x4000)
            if len(buf) == 0:
                break

            data.extend(buf)

            f.read(2) # Skip frame descriptors, even though they're needed to get record sizes

    # Get database table of content
    toc = StoreToc()
    toc.parse(data, store_header.iRef)
        
    db_schema_offset = toc.get_offset(toc.primary)
    db_schema = db_schema_struct.parse(data[db_schema_offset:])

    # Convert the schema to Construct schema
    for table in db_schema.tables:
        columns_schemas = [
            "_rowSize" / TCardinality
        ]
        for column in table.columns:
            column_schema = None
            if column.type == 0:
                column_schema = ReadBitSequence()
            elif column.type == 1:
                column_schema = Int8sl
            elif column.type == 2:
                column_schema = Int8ul
            elif column.type == 3:
                column_schema = Int16sl
            elif column.type == 4:
                column_schema = Int16ul
            elif column.type == 5:
                column_schema = Int32sl
            elif column.type == 6:
                column_schema = Int32ul
            elif column.type == 7:
                column_schema = Int64sl
            elif column.type == 8:
                column_schema = Float32l
            elif column.type == 9:
                column_schema = Float64l
            elif column.type == 10:
                column_schema = Int64sl # datetime
            elif column.type == 11:
                column_schema = PascalString(Int8ul, "cp932")
            elif column.type == 12:
                # Symbian uses SCSU for unicode strings
                column_schema = PascalString(TCardinality, "SCSU")
            elif column.type == 13:
                column_schema = Prefixed(Int8ul, GreedyBytes())
            elif column.type == 14 or column.type == 15 or column.type == 16:
                data_schema = None
                match column.type:
                    case 14:
                        data_schema = PascalString(Int8ul, "cp932")
                    case 15:
                        data_schema = PascalString(TCardinality, "SCSU")
                    case 16:
                        data_schema = Prefixed(Int8ul, GreedyBytes())
                column_schema = Struct(
                    "isInline" / ReadBitSequence(),
                    "outOfLineData" / If(not this.isInline, Struct(
                        "packedBlobId" / TCardinality,
                        "size" / TCardinality
                    )),
                    "data" / If(this.isInline, data_schema)
                )            
            else:
                raise ValueError(f"column type {column.type} not supported")
            
            if (column.attributes & 1) == 0:
                column_schema = FocusedSeq(
                    "data",
                    "exists" / ReadBitSequence(),
                    "data" / If(this.exists, column_schema)
                )
            
            # We use Optional because if there are no following entries, eof can be premature
            columns_schemas.append(column.name / Optional(column_schema))

    table_construct_schema = Struct(*columns_schemas)
    table_token_offset = toc.get_offset(table.iTokenId)
    table_token = table_token_struct.parse(data[table_token_offset:])
    cur_cluster_id = table_token.iHead
    
    jam_objects = []
    
    while cur_cluster_id != 0:
        cluster_offset = toc.get_offset(cur_cluster_id)
        cluster = cluster_struct.parse(data[cluster_offset:])
        try:
            for record_data in cluster.data:
                if record_data is None: continue
                column_data = table_construct_schema.parse(record_data)
                if column_data["appName"] == None: continue
                jam_obj = dict()
                for column in FJJAM_WANTED_COLS:
                    jam_obj[column] = column_data.get(column, None)
                jam_objects.append(jam_obj)
        except StreamError:
            # ignore incomplete entries
            pass

        cur_cluster_id = cluster.iNext & 0xFFFFFF
    
    if verbose:
        print(f"Parsed {len(jam_objects)} valid entries from the database.")
    
    return jam_objects

def convert_db_datetime(microseconds: int) -> datetime:
    # From Symbian DB:
    # It represents a date and time as a number of microseconds since midnight, January 1st, 1 AD nominal Gregorian.
    seconds = microseconds / 1_000_000
    reference_date = datetime(1, 1, 1)
    resulting_date = reference_date + timedelta(seconds=seconds)
    return resulting_date