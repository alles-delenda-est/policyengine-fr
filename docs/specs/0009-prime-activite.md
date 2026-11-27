# Spec 0009 — Prime d'activité (Stage B3)

**Status:** Implemented · **Priority:** P1 (Benefit Roadmap Stage B3) ·
**Depends on:** Specs 0001/0004 (`salaire_net`), Spec 0002 (RSA composition & resource-base pattern) ·
**Legal basis:** CSS art. L841-1 à L845-3, R842-1 à R844-5, D843-1 à D843-2

---

## 1. Problem

With RSA (Spec 0002) covering households with zero or very low income, the model still misses France's primary **in-work benefit**: the **prime d'activité** (~4.6 million beneficiary households). Without it, low- and modest-wage workers (`0.5–1.5 SMIC`) face a 100 % effective marginal withdrawal rate as RSA phases out, and their `revenu_disponible` is understated by €1,500–€3,500/year.

## 2. Statutory Formula (CSS art. L842-3, D843-1, D843-2)

Monthly on the `Famille` entity, for claimants aged ≥ 18:

```text
montant_base = max(
    ppa_montant_forfaitaire
    + taux_cumul (61 %) × revenus_activite
    + somme_bonifications_individuelles
    − ressources_foyer
    − ppa_forfait_logement,
    0
)
ppa_non_bonifiee = max(ppa_montant_forfaitaire − ressources_foyer − ppa_forfait_logement, 0)
prime_activite   = max(montant_base − ppa_non_bonifiee, 0)   # floored at 0; paid if >= 15 €/mo
```

> **Crucial statutory interaction with RSA (`ppa_non_bonifiee` subtraction, CSS art. L842-3):**
> Subtracting `max(forfaitaire − ressources − forfait_logement, 0)` ensures that a household with zero activity income gets **€0** prime d'activité (covered by RSA instead), and a household receiving both RSA and activity income receives the `61 % × revenus_activite + bonification` in-work supplement without double-counting the guaranteed floor!

### Decomposed Variables

1. `ppa_montant_forfaitaire` (`Famille`, `MONTH`): base amount (`595,25 €` Jan–Mar 2024; `622,63 €` from Apr 2024; `633,21 €` from Apr 2025) scaled by the exact same composition & parent-isolé coefficients (`+50 %`, `+30 %`, `+40 %`; `1,28412 + 0,42804 × nb_enfants`, CSS art. D843-1).
2. `ppa_forfait_logement` (`Famille`, `MONTH`): `12 %` / `16 % × 1,5` / `16,5 % × 1,8` of the *PPA* single-person base amount (CSS art. R844-4), always applied (consistent with RSA).
3. `ppa_bonification` (`Individu`, `MONTH`): individual supplement per active member aged ≥ 18 whose monthly `salaire_net` lies above `59 × SMIC_horaire_brut` (≈ 0.5 SMIC), rising linearly to `0,29101 × montant_de_base_ppa` at `120 × SMIC_horaire_brut` (≈ 1.0 SMIC) and constant above (CSS art. D843-2).
4. `ppa_base_ressources` (`Famille`, `MONTH`): total monthly family resources (`salaire_net/12 + pension_retraite_nette/12 + pensions_alimentaires_percues/12 + AF_base_reduite + ASF_forfaitisee`).
5. `prime_activite` (`Famille`, `MONTH`): assembled formula above, gated by at least one parent aged ≥ 18 and a `15 €/mois` minimum payment threshold (CSS art. D843-3), wired into `revenu_disponible`.
