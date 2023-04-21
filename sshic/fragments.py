#! /usr/bin/env python3
import re
import os
import sys
import argparse
import numpy as np
import pandas as pd
from utils import frag2, sort_by_chr

#   Set as None to avoid SettingWithCopyWarning
pd.options.mode.chained_assignment = None


def organize_contacts(
        filtered_contacts_path: str,
        probes_to_fragments_path: str
):

    """
    This function aims to organise the contacts made by each probe with the genome.
    It gives as a result a .tsv file written dataframe with on the columns the different probes
    and on the rows  the chromosomes positions contacted by the probes.

    This step may also appear annotated as the '0kb binning' as we do the same work as a re-binning function,
    but with no defined bin size.

    ARGUMENTS
    _________________
    filtered_contacts_path: str, path to the filtered contacts table of
        the current sample, made previously with the filter script
    """

    sample_filename = filtered_contacts_path.split("/")[-1]
    sample_id = re.search(r"AD\d+", sample_filename).group()
    output_dir = os.path.dirname(filtered_contacts_path)
    output_path = os.path.join(output_dir, sample_id)

    df_probes: pd.DataFrame = pd.read_csv(probes_to_fragments_path, sep='\t', index_col=0)
    fragments = pd.unique(df_probes['frag_id'].astype(str))
    df: pd.DataFrame = pd.read_csv(filtered_contacts_path, sep='\t')
    df_contacts: pd.DataFrame = pd.DataFrame(columns=['chr', 'start', 'sizes'])
    df_contacts: pd.DataFrame = df_contacts.astype(dtype={'chr': str, 'start': int, 'sizes': int})

    for x in ['a', 'b']:
        y = frag2(x)
        df2 = df[~pd.isna(df['name_' + x])]

        for frag in fragments:
            frag_int = int(frag)
            if frag_int not in pd.unique(df2['frag_'+x]):
                tmp = pd.DataFrame({
                    'chr': [np.nan],
                    'start': [np.nan],
                    'sizes': [np.nan],
                    frag: [np.nan]})

            else:
                df3 = df2[df2['frag_'+x] == frag_int]
                tmp = pd.DataFrame({
                    'chr': df3['chr_'+y],
                    'start': df3['start_'+y],
                    'sizes': df3['size_'+y],
                    frag: df3['contacts']})

            df_contacts = pd.concat([df_contacts, tmp])

    group = df_contacts.groupby(by=['chr', 'start', 'sizes'], as_index=False)
    df_res_contacts = group.sum()
    df_res_contacts = sort_by_chr(df_res_contacts, 'chr', 'start')
    df_res_contacts.index = range(len(df_res_contacts))

    df_res_frequencies = df_res_contacts.copy(deep=True)
    for frag in fragments:
        df_res_frequencies[frag] /= sum(df_res_frequencies[frag])

    #   Write into .tsv file contacts as there are and in the form of frequencies :
    df_res_contacts.to_csv(output_path + '_unbinned_contacts.tsv', sep='\t', index=False)
    df_res_frequencies.to_csv(output_path + '_unbinned_frequencies.tsv', sep='\t', index=False)


def main(argv):
    if not argv:
        print('Please enter arguments correctly')
        exit(0)

    parser = argparse.ArgumentParser(description='Contacts made by each probe with the genome (unbinned)')
    parser.add_argument('-c', '--contacts', type=str, required=True,
                        help='Path to the contacts_filtered_input.txt file (generated by filter)')
    parser.add_argument('-p', '--p2f', type=str, required=True,
                        help='Path to the probes to fragments corresponding table')

    args = parser.parse_args(argv)
    organize_contacts(args.contacts, args.p2f)


if __name__ == "__main__":
    main(sys.argv[1:])
