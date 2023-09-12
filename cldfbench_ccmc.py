import pathlib
import zipfile
import itertools

from cldfbench import Dataset as BaseDataset, CLDFSpec


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "ccmc"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        #https://zenodo.org/record/8237500/files/NHS2-metadata.csv?download=1
        #https://zenodo.org/record/8237500/files/NHS2-songs.zip?download=1
        pass

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.

        >>> args.writer.objects['LanguageTable'].append(...)
        """
        args.writer.cldf.add_component(
            'LanguageTable',
            {
                'name': 'region',
                'dc:description':
                    'indicates an approximate geographical location where the song was recorded, '
                    'using Human Relations Area Files categories '
                    '(see https://ehrafworldcultures.yale.edu)',
            }
        )
        args.writer.cldf.add_component('ParameterTable')
        args.writer.cldf.add_component('CodeTable')
        t = args.writer.cldf.add_component('MediaTable')
        t.common_props['dc:description'] = \
            "10-second excerpts of the source audio, selected at random from only portions of " \
            "the recording that contain an audible singer."
        args.writer.cldf.add_columns(
            'ValueTable',
            {'name': 'Song_ID', 'propertyUrl': '#mediaReference'},
            {'name': 'Type_ID', 'propertyUrl': '#codeReference'},
        )

        glangs = {l.id: l for l in args.glottolog.api.languoids()}
        args.writer.objects['ParameterTable'].append(dict(
            ID='song',
            Name='NHS2 song',
            Description="A Value for this parameter represents a song in the NHS discography, "
                        "coded for type using one of 10 categories.",
        ))
        seen_types = set()
        song_dir = self.cldf_dir / 'songs'
        if not song_dir.exists():
            song_dir.mkdir()
        with zipfile.ZipFile(self.raw_dir / 'NHS2-songs.zip') as songs:
            #song, type, region, glottocode
            for glottocode, rows_ in itertools.groupby(
                sorted(
                    self.raw_dir.read_csv('NHS2-metadata.csv', dicts=True),
                    key=lambda r: (r['glottocode'], r['type'], r['song'])),
                lambda r: r['glottocode'],
            ):
                rows_ = list(rows_)
                glottocode = glottocode.strip()
                glang = glangs[glottocode]
                args.writer.objects['LanguageTable'].append(dict(
                    ID=glottocode,
                    Name=glang.name,
                    Glottocode=glottocode,
                    region=rows_[0]['region'],
                    Latitude=glang.latitude,
                    Longitude=glang.longitude,
                ))
                for type, rows in itertools.groupby(rows_, lambda r: r['type']):
                    if type not in seen_types:
                        args.writer.objects['CodeTable'].append(dict(
                            ID=type,
                            Parameter_ID='song',
                            Name=type,
                        ))
                        seen_types.add(type)

                    for row in rows:
                        args.writer.objects['ValueTable'].append(dict(
                            ID=row['song'],
                            Parameter_ID='song',
                            Language_ID=glottocode,
                            Code_ID=type,
                            Value='y',
                            Song_ID=row['song'],
                        ))
                        args.writer.objects['MediaTable'].append(dict(
                            ID=row['song'],
                            Parameter_ID='song',
                            Name=row['song'],
                            Media_Type='audio/mpeg',
                            Download_URL='songs/{}.mp3'.format(row['song']),
                        ))
                        song_dir.joinpath('{}.mp3'.format(row['song'])).write_bytes(
                            songs.read('corpus_processed/{}.mp3'.format(row['song'])))
