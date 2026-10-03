"""Generate institutional/support tables from outcome-blind audited inputs."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from build_artifacts import table,integer,f,write_facts

ROOT=Path(__file__).resolve().parents[2]

def main():
    a=json.loads((ROOT/'reports/assignment2024_reconstruction.json').read_text(encoding='utf8'))
    d=pd.read_csv(ROOT/'data/processed/assignment2024_commune_paths.csv',dtype={'commune_code':str,'bassin_2022_cog2023':str,'epci_2023':str,'department':str},low_memory=False)
    counts=pd.read_csv(ROOT/'data/processed/assignment2024_territory_indicators.csv').level.value_counts()
    cuts=a['cutoffs_exact_reconstructed']
    table('assignment_thresholds',['Périmètre','Unités','Densité','Niveau de vie'],[
        ['EPCI de droit commun',integer(counts['EPCI']),f(cuts['epci_density'],2),f(cuts['epci_income'],0)],
        ['EPCI, voie montagne',integer(counts['EPCI']),f(cuts['epci_density'],2),f(cuts['epci_income_q75'],1)],
        ['Bassins de vie',integer(counts['BV2022']),f(cuts['bassin_density'],2),f(cuts['bassin_income'],0)],
        ['Départements',integer(counts['DEP']),'strictement < '+f(cuts['department_density'],0),f(cuts['department_income'],0)],
    ],widths='Xrrr')
    mandatory=d.assignment_audit_status.eq('verified_mandatory_path_listed')
    residual=d.assignment_audit_status.eq('listed_only_potential_B_or_D')
    b_only=residual&d.eligible_B_potential&~d.eligible_D_potential
    d_only=residual&~d.eligible_B_potential&d.eligible_D_potential
    both=residual&d.eligible_B_potential&d.eligible_D_potential
    table('assignment_paths',['Relation aux critères reconstruits','Dans la liste','Hors liste'],[
        ['Au moins une voie obligatoire A ou C',integer(mandatory.sum()),integer((d.assignment_audit_status=='mandatory_path_missing_from_list').sum())],
        ['Bassin seul parmi les voies restantes',integer(b_only.sum()),integer((~d.listed_initial2024&d.eligible_B_potential&~d.eligible_D_potential).sum())],
        ['Montagne possible seule',integer(d_only.sum()),integer((~d.listed_initial2024&~d.eligible_B_potential&d.eligible_D_potential).sum())],
        ['Bassin et montagne possibles',integer(both.sum()),integer((~d.listed_initial2024&d.eligible_B_potential&d.eligible_D_potential).sum())],
        ['Aucune voie possible reconstruite',integer((d.assignment_audit_status=='listed_without_reconstructed_possible_path').sum()),integer((d.assignment_audit_status=='not_listed_no_path').sum())],
        ['Total',integer(d.listed_initial2024.sum()),integer((~d.listed_initial2024).sum())],
    ],widths='Xrr')
    support=pd.read_csv(ROOT/'reports/rd_assignment_only_support.csv')
    labels={'A_income_whole_epci_barrier':'Revenu, exclusion EPCI entière',
            'B_income_commune_barrier':'Revenu, exclusion communale',
            'D_density_commune_barrier':'Densité, exclusion communale'}
    rows=[]
    for design in labels:
        z=support[support.design.eq(design)]
        rows.append([labels[design],'/'.join(f(x,0) for x in z.bandwidth),
                     '/'.join(str(x) for x in z.eligible_side_epci),'/'.join(str(x) for x in z.ineligible_side_epci)])
    table('assignment_support',['Échantillon','Rayons','Côté éligible','Autre côté'],rows,widths='Xrrr')
    q=json.loads((ROOT/'reports/data_quality.json').read_text(encoding='utf8'))
    h=json.loads((ROOT/'reports/birth_structure_quality.json').read_text(encoding='utf8'))
    hq={r['headquarters_category']:r['n'] for r in h['headquarters_categories']}
    table('measurement_benchmark',['Indicateur dans le champ stable 2019–juin 2026','Nombre'],[
        ['Immatriculations administratives',integer(q['birth_records'])],
        ['Avec état historique à la création',integer(q['births_with_historical_interval'])],
        ['À diffusion partielle, code communal utilisable',integer(q['births_with_partial_diffusion'])],
        ['Siège administratif à la création',integer(hq['headquarters'])],
        ['Non-siège à la création',integer(hq['non_headquarters'])],
        ['Statut siège inconnu',integer(h['establishment_births']-hq['headquarters']-hq['non_headquarters'])],
        ['Créations d’unités légales au siège historique localisable',integer(q['unit_birth_records_located_at_historical_headquarters'])],
    ],widths='Xr')
    vals=json.loads((ROOT/'reports/numerical_facts.json').read_text(encoding='utf8'))
    vals.update({
        'AssignmentMetroN':integer(len(d)), 'AssignmentListedN':integer(d.listed_initial2024.sum()),
        'AssignmentMandatoryN':integer(mandatory.sum()),'AssignmentResidualN':integer(residual.sum()),
        'AssignmentUnlistedN':integer((~d.listed_initial2024).sum()),
        'AssignmentBOnlyN':integer(b_only.sum()),'AssignmentDOnlyN':integer(d_only.sum()),'AssignmentBothN':integer(both.sum()),
        'AssignmentBOnlyBVN':integer(d.loc[b_only,'bassin_2022_cog2023'].nunique()),
        'EPCIIncomeCut':f(cuts['epci_income'],0),'EPCIDensityCut':f(cuts['epci_density'],2),
        'BVIncomeCut':f(cuts['bassin_income'],0),'BVDensityCut':f(cuts['bassin_density'],2),
        'IncomeRDEligibleN':integer(support[support.design.eq('B_income_commune_barrier')].eligible_side_epci.max()),
        'DensityRDEligibleN':integer(support[support.design.eq('D_density_commune_barrier')].eligible_side_epci.max()),
    })
    ca=json.loads((ROOT/'reports/review_C_assignment_paths.json').read_text(encoding='utf8'))
    vals['AssignmentFieldChecksN']=integer(ca['checked_commune_column_values'])
    rd_path=ROOT/'results/tables/bassin_rd_estimates.csv'
    if rd_path.exists():
        rd=pd.read_csv(rd_path);r=rd[rd.period.eq('primary_2024H2')&rd.bandwidth.eq(1000)].iloc[0]
        def ci(lo,hi):return '['+f(lo)+' ; '+f(hi)+']'
        table('bassin_rd_primary',['Rayon (€)','BV ≤ seuil','BV > seuil','Linéaire','Corrigé','IC RBC, HC3'],[
            [f(x.bandwidth,0),integer(x.eligible_low_income_units),integer(x.high_income_units),f(x.conventional),f(x.bias_corrected),ci(x.ci_low_hc3,x.ci_high_hc3)]
            for x in rd[rd.period.eq('primary_2024H2')].itertuples()],widths='rrrrrX')
        table('bassin_rd_clustering',['Inférence','Groupes','Erreur type','Intervalle à 95 %'],[
            ['HC3, bassins indépendants','—',f(r.se_rbc_hc3),ci(r.ci_low_hc3,r.ci_high_hc3)],
            ['Composantes des communes retenues',integer(r.joint_groups),f(r.joint_se),ci(r.joint_ci_low,r.joint_ci_high)],
            ['Composantes de tous les membres',integer(r.full_joint_groups),f(r.full_joint_se),ci(r.full_joint_ci_low,r.full_joint_ci_high)],
        ],widths='Xrrr')
        table('bassin_rd_placebos',['Second semestre','Corrigé','IC RBC, HC3','Valeur p'],[
            [x.period.replace('placebo_','').replace('H2',''),f(x.bias_corrected),ci(x.ci_low_hc3,x.ci_high_hc3),f(x.p_hc3)]
            for x in rd[rd.bandwidth.eq(1000)&rd.period.str.startswith('placebo')].itertuples()],widths='Xrrr')
        cv=pd.read_csv(ROOT/'reports/review_B_V_covariate_discontinuities_assignment_only.csv')
        cv=cv[cv.h.eq(1000)].set_index('variable')
        selected=cv.loc['selected_population_share'];old=cv.loc['old_zrr_full_population_share']
        choices={'selected_population_share':r'Population retenue (points de \%)',
                 'selected_commune_share':r'Communes retenues (points de \%)',
                 'old_zrr_full_population_share':r'Population ancienne ZRR (points de \%)',
                 'full_bv_density2020':'Densité du bassin (hab./km²)'}
        table('bassin_rd_covariates',['Caractéristique préalable','Discontinuité','IC HC3','p Holm'],[
            [label,f(cv.loc[key,'bias_corrected_jump']*(1 if 'density' in key else 100),2),
             '['+f(cv.loc[key,'hc3_ci_low']*(1 if 'density' in key else 100),2)+' ; '+f(cv.loc[key,'hc3_ci_high']*(1 if 'density' in key else 100),2)+']',
             f(cv.loc[key,'hc3_p_holm_within_h'])] for key,label in choices.items()],widths='Xrrr')
        monthly=pd.read_csv(ROOT/'results/tables/bassin_rd_monthly_diagnostics.csv');monthly['date']=pd.to_datetime(monthly.month)
        fig,ax=plt.subplots(figsize=(7.1,3.7));ax.plot(monthly.date,monthly.bias_corrected,color='#28648c',lw=1)
        ax.fill_between(monthly.date,monthly.ci_low_hc3,monthly.ci_high_hc3,color='#28648c',alpha=.18)
        ax.axhline(0,color='black',lw=.7);ax.axvspan(pd.Timestamp('2023-06-01'),pd.Timestamp('2024-06-30'),color='#b9b8ae',alpha=.17)
        ax.axvline(pd.Timestamp('2024-07-01'),color='#c45b32',lw=1);ax.set_ylabel('Discontinuité de niveau / 1 000 habitants / mois')
        ax.grid(axis='y',alpha=.15);fig.tight_layout()
        fig.savefig(ROOT/'results/figures/bassin_rd_monthly.pdf',bbox_inches='tight')
        fig.savefig(ROOT/'results/figures/bassin_rd_monthly.png',dpi=160,bbox_inches='tight');plt.close(fig)
        dep=pd.read_csv(ROOT/'results/tables/bassin_rd_dependency.csv')
        diagnostics=json.loads((ROOT/'reports/bassin_rd_results.json').read_text(encoding='utf8'))
        full=dep[dep.bandwidth.eq(1000)&dep.scope.eq('full')&dep.kind.eq('joint')].iloc[0]
        vals.update({'BVRDCoef':f(r.bias_corrected),'BVRDLo':f(r.ci_low_hc3),'BVRDHi':f(r.ci_high_hc3),
            'BVRDEligibleN':integer(r.eligible_low_income_units),'BVRDControlN':integer(r.high_income_units),
            'BVRDGroupN':integer(r.joint_groups),'BVRDFullGroupN':integer(r.full_joint_groups),
            'BVRDCoverageJump':f(100*selected.bias_corrected_jump,1),'BVRDCoverageLo':f(100*selected.hc3_ci_low,1),
            'BVRDCoverageHi':f(100*selected.hc3_ci_high,1),'BVRDCoverageHolmP':f(selected.hc3_p_holm_within_h),
            'BVRDOldShareJump':f(100*old.bias_corrected_jump,1),'BVRDFullMaxShare':f(100*full.max_group_share,1),
            'BVRDCovariateN':integer(len(cv)),
            'BVRDTestableCovN':integer(cv.status.eq('estimated_assignment_covariate_only').sum()),
            'BVRDPreN':integer(diagnostics['pre_months']),
            'BVRDClusterRank':integer(diagnostics['pre_joint_diagnostics']['joint_CR1']['covariance_rank']),
            'BVRDFullRank':integer(diagnostics['pre_joint_diagnostics']['full_joint_CR1']['covariance_rank'])})
    write_facts(vals)
    print('Institutional, assignment support and measurement tables generated; no new outcome estimation.')

if __name__=='__main__':main()
