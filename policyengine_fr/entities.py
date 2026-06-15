"""
Entities for the French tax-benefit system.

France distinguishes several overlapping groupings of people, and most
French variables are naturally computed on one of them. We model the four
canonical entities used by OpenFisca-France:

- ``individu``      — a single person (the only ``is_person`` entity).
- ``foyer_fiscal``  — the income-tax household (the unit that files one
                      *déclaration de revenus*); up to two ``declarants``
                      plus their ``personnes_a_charge``.
- ``famille``       — the unit used for most CAF/MSA benefits
                      (allocations familiales, etc.).
- ``menage``        — the household sharing a dwelling (used for housing
                      and consumption concepts).

See https://openfisca.org/doc/key-concepts/person,_entities,_role.html

NOTE: roles below are an initial design. As benefits are added (esp. CAF
benefits on ``famille``), revisit role keys and max counts.
"""

from policyengine_core.entities import build_entity

Individu = build_entity(
    key="individu",
    plural="individus",
    label="Personne",
    doc="Une personne physique.",
    is_person=True,
)

FoyerFiscal = build_entity(
    key="foyer_fiscal",
    plural="foyers_fiscaux",
    label="Foyer fiscal",
    doc="Le foyer fiscal: l'unité qui dépose une déclaration de revenus.",
    roles=[
        {
            "key": "declarant",
            "plural": "declarants",
            "label": "Déclarant",
            "max": 2,
            "doc": "Les déclarants du foyer fiscal (au plus deux).",
        },
        {
            "key": "personne_a_charge",
            "plural": "personnes_a_charge",
            "label": "Personne à charge",
            "doc": "Les personnes rattachées au foyer fiscal.",
        },
    ],
)

Famille = build_entity(
    key="famille",
    plural="familles",
    label="Famille",
    doc="La famille au sens des prestations sociales (CAF/MSA).",
    roles=[
        {
            "key": "parent",
            "plural": "parents",
            "label": "Parent",
            "max": 2,
            "doc": "Les parents de la famille (au plus deux).",
        },
        {
            "key": "enfant",
            "plural": "enfants",
            "label": "Enfant",
            "doc": "Les enfants de la famille.",
        },
    ],
)

Menage = build_entity(
    key="menage",
    plural="menages",
    label="Ménage",
    doc="Le ménage: l'ensemble des occupants d'un même logement.",
    roles=[
        {
            "key": "personne_de_reference",
            "plural": "personnes_de_reference",
            "label": "Personne de référence",
            "max": 1,
            "doc": "La personne de référence du ménage.",
        },
        {
            "key": "conjoint",
            "plural": "conjoints",
            "label": "Conjoint",
            "max": 1,
            "doc": "Le conjoint de la personne de référence.",
        },
        {
            "key": "enfant",
            "plural": "enfants",
            "label": "Enfant",
            "doc": "Les enfants du ménage.",
        },
        {
            "key": "autre",
            "plural": "autres",
            "label": "Autre",
            "doc": "Les autres occupants du logement.",
        },
    ],
)


entities = [Individu, FoyerFiscal, Famille, Menage]
