# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: fl.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x08\x66l.proto\"\'\n\x0e\x41verageRequest\x12\x15\n\rlocal_average\x18\x01 \x01(\x01\")\n\x0f\x41verageResponse\x12\x16\n\x0eglobal_average\x18\x01 \x01(\x01\"\x07\n\x05\x45mpty2|\n\x11\x46\x65\x64\x65ratedLearning\x12\x37\n\x10SendLocalAverage\x12\x0f.AverageRequest\x1a\x10.AverageResponse\"\x00\x12.\n\x10GetGlobalAverage\x12\x06.Empty\x1a\x10.AverageResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'fl_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_AVERAGEREQUEST']._serialized_start=12
  _globals['_AVERAGEREQUEST']._serialized_end=51
  _globals['_AVERAGERESPONSE']._serialized_start=53
  _globals['_AVERAGERESPONSE']._serialized_end=94
  _globals['_EMPTY']._serialized_start=96
  _globals['_EMPTY']._serialized_end=103
  _globals['_FEDERATEDLEARNING']._serialized_start=105
  _globals['_FEDERATEDLEARNING']._serialized_end=229
# @@protoc_insertion_point(module_scope)
