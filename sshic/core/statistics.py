import os
import sys
import argparse
import numpy as np
import pandas as pd


def get_stats(
        contacts_unbinned_path: str,
        sparse_contacts_path: str,
        oligos_path: str,
        output_dir: str,
        cis_range: int = 50000,
):
    """
    Generate statistics and normalization for contacts made by each probe.

    Parameters
    ----------
    contacts_unbinned_path : str
        Path to the unbinned_contacts.tsv file (generated by fragments).
    sparse_contacts_path : str
        Path to the sparse_contacts_input.txt file (generated by hicstuff).
    oligos_path : str
        Path to the oligos input CSV file.
    cis_range: int, default=5000
        Cis range to be considered around the probe.
    output_dir : str
        Path to the output directory.
    """

    sample_filename = contacts_unbinned_path.split("/")[-1]
    sample_id = sample_filename.split("_")[0]
    # sample_id = re.search(r"AD\d+[A-Z]*", sample_filename).group()
    output_path = os.path.join(output_dir, sample_id)

    df_probes: pd.DataFrame = pd.read_csv(oligos_path, sep=',')

    chr_size_dict: dict = {
        'chr1': 230218, 'chr2': 813184, 'chr3': 316620, 'chr4': 1531933, 'chr5': 576874, 'chr6': 270161,
        'chr7': 1090940, 'chr8': 562643, 'chr9': 439888, 'chr10': 745751, 'chr11': 666816, 'chr12': 1078177,
        'chr13': 924431, 'chr14': 784333, 'chr15': 1091291, 'chr16': 948066, 'mitochondrion': 85779, '2_micron': 6318}

    chr_list = list(chr_size_dict.keys())

    df_unbinned_contacts: pd.DataFrame = pd.read_csv(contacts_unbinned_path, sep='\t')
    df_unbinned_contacts = df_unbinned_contacts.astype(dtype={'chr': str, 'start': int, 'sizes': int})

    df_sparse_contacts: pd.DataFrame = \
        pd.read_csv(sparse_contacts_path, header=0, sep="\t", names=['frag_a', 'frag_b', 'contacts'])
    #   from sparse_matrix (hicstuff results): get total contacts from which probes enrichment is calculated
    total_sparse_contacts = sum(df_sparse_contacts["contacts"])

    chr_contacts_nrm = {k: [] for k in chr_size_dict}
    chr_inter_only_contacts_nrm = {k: [] for k in chr_size_dict}

    df_stats: pd.DataFrame = pd.DataFrame(columns=[
        "probe", "chr", "fragment", "type", "contacts",
        "coverage_over_hic_contacts", "cis", "trans",
        "intra_chr", "inter_chr"])

    probes = df_probes['name'].to_list()
    fragments = df_probes['fragment'].astype(str).to_list()
    for index, (probe, frag) in enumerate(zip(probes, fragments)):
        df_stats.loc[index, "probe"] = probe
        df_stats.loc[index, "fragment"] = frag
        df_stats.loc[index, "type"] = df_probes.loc[index, "type"]
        self_chr = df_probes.loc[index, "chr"]
        df_stats.loc[index, "chr"] = self_chr

        sub_df = df_unbinned_contacts[['chr', 'start', 'sizes', frag]]
        sub_df.insert(3,  'end', sub_df['start'] + sub_df['sizes'])
        cis_limits = [
            int(df_probes.loc[index, 'start']) - cis_range,
            int(df_probes.loc[index, 'end']) + cis_range
        ]
        probe_contacts = sub_df[frag].sum()
        df_stats.loc[index, "contacts"] = probe_contacts
        df_stats.loc[index, 'coverage_over_hic_contacts'] = probe_contacts / total_sparse_contacts
        probes_contacts_inter = sub_df.query("chr != @self_chr")[frag].sum()

        if probe_contacts > 0:
            cis_freq = sub_df.query("chr == @self_chr & start >= @cis_limits[0] & end <= @cis_limits[1]")[frag].sum()
            cis_freq /= probe_contacts

            trans_freq = 1 - cis_freq
            inter_chr_freq = probes_contacts_inter / probe_contacts
            intra_chr_freq = 1 - inter_chr_freq
        else:
            cis_freq = 0
            trans_freq = 0
            inter_chr_freq = 0
            intra_chr_freq = 0

        df_stats.loc[index, "cis"] = cis_freq
        df_stats.loc[index, "trans"] = trans_freq
        df_stats.loc[index, "intra_chr"] = intra_chr_freq
        df_stats.loc[index, "inter_chr"] = inter_chr_freq

        for chrom in chr_list:
            #   n1: sum contacts chr_i
            #   d1: sum contacts all chr
            #   chrom_size: chr_i's size
            #   genome_size: sum of sizes for all chr except frag_chr
            #   c1: normalized contacts on chr_i for frag_j
            chrom_size = chr_size_dict[chrom]
            genome_size = sum([s for c, s in chr_size_dict.items() if c != self_chr])
            n1 = sub_df.loc[sub_df['chr'] == chrom, frag].sum()
            if n1 == 0:
                chr_contacts_nrm[chrom].append(0)
            else:
                d1 = probe_contacts
                c1 = (n1/d1) / (chrom_size/genome_size)
                chr_contacts_nrm[chrom].append(c1)

            #   n2: sum contacts chr_i if chr_i != probe_chr
            #   d2: sum contacts all inter chr (exclude the probe_chr)
            #   c2: normalized inter chr contacts on chr_i for frag_j
            n2 = sub_df.loc[
                (sub_df['chr'] == chrom) &
                (sub_df['chr'] != self_chr), frag].sum()

            if n2 == 0:
                chr_inter_only_contacts_nrm[chrom].append(0)
            else:
                d2 = probes_contacts_inter
                c2 = (n2 / d2) / (chrom_size / genome_size)
                chr_inter_only_contacts_nrm[chrom].append(c2)

    #  capture_efficiency_vs_dsdna: amount of contact for one oligo divided
    #  by the mean of all other 'ds' oligos in the genome
    n3 = df_stats.loc[:, 'contacts']
    d3 = np.mean(df_stats.loc[df_stats['type'] == 'ds', 'contacts'])
    df_stats['dsdna_norm_capture_efficiency'] = n3 / d3

    df_chr_nrm = pd.DataFrame({
        "probe": probes, "fragment": fragments, "type": df_probes["type"].values
    })

    df_chr_inter_only_nrm = df_chr_nrm.copy(deep=True)

    for chr_id in chr_list:
        df_chr_nrm[chr_id] = chr_contacts_nrm[chr_id]
        df_chr_inter_only_nrm[chr_id] = chr_inter_only_contacts_nrm[chr_id]

    df_stats.sort_values(by="fragment", ascending=True, inplace=True)
    df_chr_nrm.sort_values(by="fragment", ascending=True, inplace=True)
    df_chr_inter_only_nrm.sort_values(by="fragment", ascending=True, inplace=True)

    df_stats.to_csv(output_path + '_global_statistics.tsv', sep='\t')
    df_chr_nrm.to_csv(output_path + '_normalized_chr_freq.tsv', sep='\t')
    df_chr_inter_only_nrm.to_csv(output_path + '_normalized_inter_chr_freq.tsv', sep='\t')


def compare_to_wt(statistics_path: str, reference_path: str, wt_ref_name: str):
    """
    wt_reference: Optional[str], default=None
            Path to the wt_capture_efficiency file (Optional, if you want to weighted sample).
    """
    df_stats: pd.DataFrame = pd.read_csv(statistics_path, header=0, sep="\t", index_col=0)
    df_wt: pd.DataFrame = pd.read_csv(reference_path, sep='\t')
    df_stats[f"capture_efficiency_vs_{wt_ref_name}"] = np.nan
    for index, row in df_stats.iterrows():
        probe = row['probe']
        wt_capture_eff = df_wt.loc[df_wt['probe'] == probe, "dsdna_norm_capture_efficiency"].tolist()[0]

        if wt_capture_eff > 0:
            df_stats.loc[index, f"capture_efficiency_vs_{wt_ref_name}"] = \
                df_stats.loc[index, 'dsdna_norm_capture_efficiency'] / wt_capture_eff

    df_stats.to_csv(statistics_path, sep='\t')


def main(argv):
    """
    Main function to parse command-line arguments and execute the get_stats function.

    Parameters
    ----------
    argv : List[str]
        List of command-line arguments.
    """
    if not argv:
        print('Please enter arguments correctly')
        exit(0)

    parser = argparse.ArgumentParser(
        description='Making some statistics and normalization around the contacts made for each probe')
    parser.add_argument('-u', '--contacts', type=str, required=True,
                        help='Path to the unbinned_contacts.tsv file (generated by fragments)')
    parser.add_argument('-s', '--sparse', type=str, required=True,
                        help='Path to the sparse_contacts_input.txt file (generated by hicstuff)')
    parser.add_argument('--oligos', type=str, required=True,
                        help='Path to the oligos_input.csv file')
    parser.add_argument('-w', '--wildtype', type=str,
                        help='Path to the wt_capture_efficiency file (Optional, if you want to weighted sample)')

    args = parser.parse_args(argv)

    get_stats(
        contacts_unbinned_path=args.contacts,
        sparse_contacts_path=args.sparse,
        oligos_path=args.oligos,
        output_dir=os.path.dirname(args.contacts)
    )


if __name__ == "__main__":
    main(sys.argv[1:])
