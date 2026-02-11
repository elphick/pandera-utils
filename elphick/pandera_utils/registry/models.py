from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Variable(Base):
    """Represents a reusable field/column definition for pandera schemas.

    A Variable captures the shared, schema-agnostic aspects of a column,
    such as its name, data type, nullability, and general description.
    Schema-specific overrides or options are stored in SchemaField.
    """

    __tablename__ = "variables"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    data_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    nullable = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    schema_links = relationship(
        "SchemaField",
        back_populates="variable",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Variable(name={self.name!r}, data_type={self.data_type!r})>"


class Schema(Base):
    """Represents a logical pandera schema (e.g. a DataFrameSchema).

    A Schema groups variables into a coherent structure. The relationship
    between Schema and Variable is many-to-many and implemented via
    the SchemaField association table.
    """

    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True)

    source_id = Column(
        Integer,
        ForeignKey("schema_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    source = relationship("SchemaSource", back_populates="schemas")

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    metadata = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    fields = relationship(
        "SchemaField",
        back_populates="schema",
        cascade="all, delete-orphan",
        order_by="SchemaField.position",
    )

    def __repr__(self) -> str:
        return f"<Schema(name={self.name!r})>"


class SchemaField(Base):
    """Associates a Variable with a Schema and stores context-specific settings.

    This is an association object that represents one column of a schema
    and how that column behaves in that specific schema context
    (e.g., required/optional, position, any field-level overrides).
    """

    __tablename__ = "schema_fields"

    id = Column(Integer, primary_key=True)
    schema_id = Column(
        Integer,
        ForeignKey("schemas.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id = Column(
        Integer,
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Optional ordering of fields within a schema.
    position = Column(Integer, nullable=True)

    # Whether this field is required for this particular schema.
    required = Column(Boolean, default=True, nullable=False)

    # Context-specific options or overrides (e.g., default value, alias,
    # schema-specific checks). Variable.metadata can store shared aspects.
    metadata = Column(JSON, nullable=True)

    schema = relationship("Schema", back_populates="fields")
    variable = relationship("Variable", back_populates="schema_links")

    __table_args__ = (
        UniqueConstraint(
            "schema_id",
            "variable_id",
            name="uq_schema_variable",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SchemaField(schema_id={self.schema_id}, "
            f"variable_id={self.variable_id}, required={self.required})>"
        )


class SchemaSource(Base):
    """Represents the origin of a schema, typically a YAML file.

    This allows reconstruction of the original file structure when exporting
    schemas back into YAML.
    """

    __tablename__ = "schema_sources"

    id = Column(Integer, primary_key=True)

    # absolute or project-relative file path as string
    path = Column(String(1024), nullable=False, unique=True)

    # optional grouping/tag for future use
    group_name = Column(String(255), nullable=True)

    schemas = relationship(
        "Schema",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SchemaSource(path={self.path!r})>"
