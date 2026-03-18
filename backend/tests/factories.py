"""Factory Boy factories for test data generation.

Uses SQLAlchemyModelFactory to create ORM objects directly in the DB,
bypassing HTTP calls for faster, more focused tests.

All user-facing fake data uses the 'pt_BR' Faker locale.
"""

import uuid
from datetime import date
from decimal import Decimal

import factory
from faker import Faker

from app.models import (
    CategoriaTransacao,
    Client,
    DocumentType,
    Fornecedor,
    FornecedorCategoria,
    FornecedorCategoryEnum,
    FornecedorContato,
    ItemType,
    Product,
    ProductCategory,
    ProductItem,
    ProductItemStatus,
    ProductType,
    Service,
    ServiceItem,
    ServiceType,
    TipoTransacao,
    Transacao,
)

fake = Faker("pt_BR")


class FornecedorFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a Fornecedor (supplier) directly in the database."""

    class Meta:
        model = Fornecedor
        sqlalchemy_session = None  # set at runtime via conftest fixture
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    company_name = factory.LazyFunction(fake.company)
    cnpj = factory.LazyFunction(
        lambda: fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
    )
    address = factory.LazyFunction(fake.address)
    notes = factory.LazyFunction(lambda: fake.sentence(nb_words=6))


class FornecedorContatoFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a FornecedorContato (supplier contact) directly in the database."""

    class Meta:
        model = FornecedorContato
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    fornecedor = factory.SubFactory(FornecedorFactory)
    fornecedor_id = factory.LazyAttribute(lambda o: o.fornecedor.id)
    name = factory.LazyFunction(fake.name)
    telefone = factory.LazyFunction(fake.phone_number)
    whatsapp = factory.LazyFunction(fake.phone_number)
    description = factory.LazyFunction(lambda: fake.job()[:100])


class FornecedorCategoriaFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a FornecedorCategoria (supplier category link) directly in the database."""

    class Meta:
        model = FornecedorCategoria
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    fornecedor = factory.SubFactory(FornecedorFactory)
    fornecedor_id = factory.LazyAttribute(lambda o: o.fornecedor.id)
    category = factory.LazyFunction(
        lambda: fake.random_element(elements=[e.value for e in FornecedorCategoryEnum])
    )


# ── Client ─────────────────────────────────────────────────────────────────────


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a Client directly in the database."""

    class Meta:
        model = Client
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyFunction(fake.name)
    document_type = DocumentType.cpf
    document_number = factory.LazyFunction(
        lambda: fake.cpf().replace(".", "").replace("-", "")
    )
    email = factory.LazyFunction(fake.email)
    phone = factory.LazyFunction(fake.phone_number)
    address = factory.LazyFunction(fake.address)


# ── Service ────────────────────────────────────────────────────────────────────


class ServiceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a Service directly in the database.

    Auto-creates a Client via SubFactory if no client/client_id is provided.
    """

    class Meta:
        model = Service
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    type = ServiceType.perfuracao
    execution_address = factory.LazyFunction(fake.address)
    client = factory.SubFactory(ClientFactory)
    client_id = factory.LazyAttribute(lambda o: o.client.id)


class ServiceItemFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a ServiceItem directly in the database.

    Auto-creates a Service (and Client) via SubFactory if no service is provided.
    """

    class Meta:
        model = ServiceItem
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    item_type = ItemType.material
    description = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
    quantity = 10.0
    unit_price = Decimal("15.50")
    service = factory.SubFactory(ServiceFactory)
    service_id = factory.LazyAttribute(lambda o: o.service.id)


# ── Estoque (Inventory) ───────────────────────────────────────────────────────


class ProductTypeFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a ProductType directly in the database."""

    class Meta:
        model = ProductType
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    category = ProductCategory.tubos
    name = factory.LazyFunction(lambda: f"Tubo Teste {uuid.uuid4().hex[:6]}")
    unit_of_measure = "un"


class ProductFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a Product directly in the database.

    Auto-creates a ProductType via SubFactory if not provided.
    """

    class Meta:
        model = Product
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    product_type = factory.SubFactory(ProductTypeFactory)
    product_type_id = factory.LazyAttribute(lambda o: o.product_type.id)
    name = factory.LazyFunction(lambda: f"Produto {uuid.uuid4().hex[:6]}")
    unit_price = Decimal("10.00")


class ProductItemFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a ProductItem directly in the database.

    Auto-creates a Product (and ProductType) via SubFactory if not provided.
    """

    class Meta:
        model = ProductItem
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    product = factory.SubFactory(ProductFactory)
    product_id = factory.LazyAttribute(lambda o: o.product.id)
    quantity = Decimal("5.0")
    status = ProductItemStatus.em_estoque


# ── Financeiro ─────────────────────────────────────────────────────────────────


class TransacaoFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create a Transacao directly in the database."""

    class Meta:
        model = Transacao
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid.uuid4)
    tipo = TipoTransacao.receita
    categoria = CategoriaTransacao.SERVICO
    valor = Decimal("1000.00")
    data_competencia = factory.LazyFunction(lambda: date.today())
    descricao = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
