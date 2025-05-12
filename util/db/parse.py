from definitions import *
from constants import FJJAM_WANTED_COLS

def extract_columns(fjjam_path: os.PathLike, verbose=False):
    # Author: usernameak | /bin/cat
    with open(fjjam_path, "rb") as f:
        checked_uid = checked_uid_struct.parse(f.read(16))
        store_header = store_header_struct.parse(f.read(16))
        print(store_header)

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
    if verbose:
        print(f"Got {toc.num_entries()} entries!")
        
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
    
    while cur_cluster_id != 0:
        cluster_offset = toc.get_offset(cur_cluster_id)
        cluster = cluster_struct.parse(data[cluster_offset:])
        try:
            for record_data in cluster.data:
                if record_data is None: continue
                column_data = table_construct_schema.parse(record_data)
                if column_data["appName"] == None: continue
                for column in FJJAM_WANTED_COLS:
                    print(column, ": ", column_data[column])
        except StreamError:
            # ignore incomplete entries
            pass

        cur_cluster_id = cluster.iNext & 0xFFFFFF
    
    