#! /usr/bin/env python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import re


def get_nfr_contacts(
        fragments_path: str,
        nucleosomes_path: str,
        output_path: str):

    df_fragments = pd.read_csv(fragments_path, sep='\t')
    df_fragments.insert(0, 'uid', df_fragments.index)
    df_nucleosomes = pd.read_csv(nucleosomes_path, sep='\t')
    df_nucleosomes.drop_duplicates(keep='first', inplace=True)
    df_nucleosomes.index = range(len(df_nucleosomes))
    excluded_chr = ['2_micron', 'mitochondrion', 'chr_artificial']
    df_fragments = df_fragments[~df_fragments['chrom'].isin(excluded_chr)]
    df_fragments["midpoint"] = (df_fragments["end_pos"] + df_fragments["start_pos"]) / 2
    df_merged = pd.merge(df_fragments, df_nucleosomes, on='chrom')
    df_merged_in_nfr = df_merged[(df_merged.midpoint >= df_merged.start) & (df_merged.midpoint <= df_merged.end)]

    index_in_nfr = np.unique(df_merged_in_nfr.uid)
    df_fragments_in_nfr = df_fragments.loc[index_in_nfr, :]
    df_fragments_out_nfr = df_fragments.drop(index_in_nfr)

    df_fragments.drop(columns='uid', inplace=True)
    df_fragments_in_nfr.to_csv(output_path + 'fragments_list_in_nfr.tsv', sep='\t', index_label='fragments')
    df_fragments_out_nfr.to_csv(output_path + 'fragments_list_out_nfr.tsv', sep='\t', index_label='fragments')

    return df_fragments_in_nfr, df_fragments_out_nfr


def nfr_statistics(
        df_contacts: pd.DataFrame,
        df_probes: pd.DataFrame,
        df_fragments_in: pd.DataFrame,
        df_fragments_out: pd.DataFrame,
        output_path: str):

    df_contacts_in = df_contacts[df_contacts['positions'].isin(df_fragments_in['start_pos'])]
    df_contacts_out = df_contacts[df_contacts['positions'].isin(df_fragments_out['start_pos'])]
    all_probes = df_probes.columns.tolist()

    probes = []
    fragments = []
    types = []
    nfr_in = []
    nfr_out = []
    total_sizes_in = sum(df_fragments_in['size'].values)
    total_sizes_out = sum(df_fragments_out['size'].values)
    total_sizes_all = total_sizes_in + total_sizes_out
    ii_probe = 0
    for probe in all_probes:
        probe_type, probe_start, probe_end, probe_chr, frag, frag_start, frag_end = df_probes[probe].tolist()
        if frag not in df_contacts.columns:
            continue
        probes.append(probe)
        fragments.append(frag)
        types.append(probe_type)
        #   cts_in:  sum of contacts made by the probe inside nfr
        #   cts_out: sum of contacts made by the probe outside nfr
        cts_in = np.sum(df_contacts_in[frag].values)
        cts_out = np.sum(df_contacts_out[frag].values)

        nfr_in.append(
            (cts_in / (cts_in + cts_out)) / (total_sizes_in / total_sizes_all)
        )

        nfr_out.append(
            (cts_out / (cts_in + cts_out)) / (total_sizes_out / total_sizes_all)
        )
        ii_probe += 1

    df_stats = pd.DataFrame({'probe': probes, 'fragment': fragments, 'type': types,
                             'contacts_in_nfr': nfr_in, 'contacts_out_nfr': nfr_out})

    df_stats.to_csv(output_path + '_statistics_nfr_per_probe.tsv', sep='\t')


def plot_size_distribution(
        df_fragments: pd.DataFrame,
        mode: str,
        output_path: str):

    x = df_fragments['size'].values

    #   Freedman-Diaconis rule for optimal binning
    q1 = np.quantile(x, 0.25)
    q3 = np.quantile(x, 0.75)
    iqr = q3 - q1
    bin_width = (2 * iqr) / (len(x) ** (1 / 3))
    bin_count = int(np.ceil((x.max() - x.min()) / bin_width))

    xx = np.linspace(min(x), max(x), 10000)
    kde = stats.gaussian_kde(x)
    fig, ax = plt.subplots(figsize=(16, 14), dpi=300)
    ax.hist(x, density=True, bins=bin_count, alpha=0.3, linewidth=1.2, edgecolor='black')
    ax.plot(xx, kde(xx))
    plt.xlabel('Sizes of fragments')
    plt.ylabel('Numbers of contacts')
    plt.title("Distribution of fragments sizes {0} NFR".format(mode))
    plt.savefig(output_path + 'fragments_sizes_{0}_nfr_distribution.jpg'.format(mode), dpi=300)
    # plt.show()
    plt.close()


def preprocess(
        fragments_list_path: str,
        nucleosomes_path,
        output_dir: str):

    df_fragments_in_nfr, df_fragments_out_nfr = get_nfr_contacts(
        fragments_path=fragments_list_path,
        nucleosomes_path=nucleosomes_path,
        output_path=output_dir
    )

    plot_size_distribution(
        df_fragments=df_fragments_in_nfr,
        mode='inside',
        output_path=output_dir
    )

    plot_size_distribution(
        df_fragments=df_fragments_out_nfr,
        mode='outside',
        output_path=output_dir
    )


def run(
        formatted_contacts_path: str,
        probes_to_fragments_path: str,
        fragments_in_nfr_path: str,
        fragments_out_nfr_path: str,
        output_dir: str):

    df_contacts = pd.read_csv(formatted_contacts_path, sep='\t', index_col=False)
    df_probes = pd.read_csv(probes_to_fragments_path, sep='\t', index_col=0)
    sample_id = re.search(r"AD\d+", formatted_contacts_path).group()

    df_fragments_in_nfr = pd.read_csv(fragments_in_nfr_path, sep='\t', index_col=0)
    df_fragments_out_nfr = pd.read_csv(fragments_out_nfr_path, sep='\t', index_col=0)

    nfr_statistics(
        df_contacts=df_contacts,
        df_probes=df_probes,
        df_fragments_in=df_fragments_in_nfr,
        df_fragments_out=df_fragments_out_nfr,
        output_path=output_dir+sample_id
    )

    print('DONE: ', sample_id)
