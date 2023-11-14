import pathlib
import zipfile
import itertools

from pydplace.dataset import DatasetWithSocieties, data_schema
from clldutils.markup import add_markdown_text
from clldutils.path import git_describe

TYPES = [  # Label, Inclusion criteria, Exclusion criteria
    ('DANCE',
     'Sung with the goal of a person or persons dancing along to it.',
     'Songs that happen to be accompanied by dancing but are used for other goals.',
    ),
    ('HEALING',
     'Sung in a healing ceremony with the goal of curing sickness.',
     'Songs describing sick people or a past epidemic.',
     ),
    ('LOVE',
     'Sung to express love directly to another person or to describe currently felt love.',
     'Songs about unrequited love, deceased loved ones, or love for animals or property.',
     ),
    ('LULLABY',
     'Sung to an infant or child with the goal of soothing, calming, or putting to sleep.',
     'Songs designed to excite the listener (e.g., "play songs"); singing games.',
     ),
    ('PLAY',
     'A song that excites a child or infant and engages them in play. '
     'This can include singing games.',
     "Children's songs for soothing, calming, or putting to sleep.",
     ),
    ('PROCESSION',
     'Sung to accompany a formalized march, entrance, or parade, such as during a wedding, '
     'funeral or the introduction of a leader.',
     'Processions of dancing.',
     ),
    ('MOURNING',
     'Sung to express grief or sadness about the death of a person, in the present or past.',
     'Songs for sick or dying people (these are more likely to be healing songs), or laments '
     'about events other than the death of a person.',
     ),
    ('WORK',
     'Sung to accompany work activities, including planting, grinding, harvesting, processing, '
     'tool-making.',
     'Hunting songs (esp. songs sung to celebrate successful hunts, songs sung to prepare for hunts).',
     ),
    ('STORY',
     'Sung to recount historical or mythological events, narrate a sequence of activities '
     'by one or more persons, etc. (e.g., a ballad).',
     'Lullabies that include stories.',
     ),
    ('PRAISE',
     'Sung to express admiration for the traits or accomplishments of a person, animal, '
     'location, or item of property.',
     'A song expressing love for another person or explicitly religious songs (like devotionals).',
     ),
]


class Dataset(DatasetWithSocieties):
    dir = pathlib.Path(__file__).parent
    id = "dplace-dataset-ccmc"

    def cmd_download(self, args):
        self.raw_dir.download(
            'https://zenodo.org/record/8237500/files/NHS2-metadata.csv?download=1',
            'NHS2-metadata.csv')
        self.raw_dir.download(
            'https://zenodo.org/record/8237500/files/NHS2-songs.zip?download=1',
            'NHS2-songs.zip')

    def cmd_makecldf(self, args):
        assert git_describe(self.raw_dir / 'glottolog-cldf') == args.glottolog_version
        data_schema(args.writer.cldf)  # Add schema for data.
        self.schema(args.writer.cldf)  # Add schema for societies.
        # Add custom schema:
        args.writer.cldf.add_columns(
            'LanguageTable',
            {
                'name': 'HRAF_region',
                'dc:description':
                    'indicates an approximate geographical location where the song was recorded, '
                    'using Human Relations Area Files categories '
                    '(see https://ehrafworldcultures.yale.edu)',
            }
        )
        args.writer.cldf['CodeTable'].common_props['dc:description'] = \
            ("The codes for the single parameter 'CCMC1' are the 10 categories, describing song "
             "type.")
        t = args.writer.cldf.add_component('MediaTable')
        t.common_props['dc:description'] = \
            "10-second excerpts of the source audio, selected at random from only portions of " \
            "the recording that contain an audible singer."
        args.writer.cldf.add_columns(
            'ValueTable',
            {
                'name': 'Song_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference'},
        )
        args.writer.cldf['LanguageTable'].common_props['dc:description'] = '{}\n{}'.format(
            args.writer.cldf['LanguageTable'].common_props['dc:description'],
            "Note that a society's name and location in this dataset is taken from the "
            'corresponding language or dialect in Glottolog.'
        )

        glangs = {
            l['ID']: l for l in
            self.raw_dir.joinpath('glottolog-cldf', 'cldf').read_csv('languages.csv', dicts=True)}
        etclangs = {r['glottocode']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)}

        args.writer.objects['ParameterTable'].append(dict(
            ID=self.with_prefix(1),
            Name='NHS2 song',
            Description="A Value for this parameter represents a song in the NHS discography, "
                        "coded for type using one of 10 categories.",
        ))
        seen_types = set()
        known_types = {label.capitalize(): (incl, excl) for label, incl, excl in TYPES}
        song_dir = self.cldf_dir / 'songs'
        if not song_dir.exists():
            song_dir.mkdir()
        with zipfile.ZipFile(self.raw_dir / 'NHS2-songs.zip') as songs:
            # song, type, region, glottocode
            for glottocode, rows_ in itertools.groupby(
                    sorted(
                        self.raw_dir.read_csv('NHS2-metadata.csv', dicts=True),
                        key=lambda r: (r['glottocode'], r['type'], r['song'])),
                    lambda r: r['glottocode'],
            ):
                rows_ = list(rows_)
                glottocode = glottocode.strip()
                glang = glangs[glottocode]
                loc = etclangs.get(glottocode, glang)

                self.add_society(
                    args.writer,
                    ID=self.with_prefix(glottocode),
                    Name=glang['Name'],
                    Glottocode=glottocode,
                    Latitude=loc['Latitude'],
                    Longitude=loc['Longitude'],
                )

                for type, rows in itertools.groupby(rows_, lambda r: r['type']):
                    if type not in seen_types:
                        args.writer.objects['CodeTable'].append(dict(
                            ID=self.with_prefix('1-{}'.format(type)),
                            Var_ID=self.with_prefix(1),
                            Name=type,
                            Description='Inclusion criteria: {}\nExclusion criteria: {}'.format(
                                *known_types[type])
                        ))
                        seen_types.add(type)

                    for row in rows:
                        args.writer.objects['ValueTable'].append(dict(
                            ID=row['song'],
                            Var_ID=self.with_prefix(1),
                            Soc_ID=self.with_prefix(glottocode),
                            Code_ID=self.with_prefix('1-{}'.format(type)),
                            Value=type,
                            Song_ID=row['song'],
                        ))
                        args.writer.objects['MediaTable'].append(dict(
                            ID=row['song'],
                            Name=row['song'],
                            Media_Type='audio/mpeg',
                            Download_URL='songs/{}.mp3'.format(row['song']),
                        ))
                        song_dir.joinpath('{}.mp3'.format(row['song'])).write_bytes(
                            songs.read('corpus_processed/{}.mp3'.format(row['song'])))

    def cmd_readme(self, args):
        return add_markdown_text(
            super().cmd_readme(args),
            """### Coverage

![](map.png)

### Data model

See [cldf/README.md](cldf) for a description of the tables and columns and the
entity-relationship diagram below for how they relate.

![](erd.svg)""",
            section='Description')
