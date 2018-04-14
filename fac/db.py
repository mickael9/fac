import os.path
import time

from appdirs import user_cache_dir

from whoosh import qparser, analysis
from whoosh.query import Query
from whoosh.sorting import MultiFacet, FieldFacet
from whoosh.fields import columns, Schema, FieldType, TEXT, NUMERIC, ID

from whoosh.filedb.filestore import FileStorage
from whoosh.index import EmptyIndexError

from fac.files import JSONFile
from fac.utils import JSONDict, ProgressWidget

normal_analyzer = analysis.StandardAnalyzer()
intra_analyzer = (analysis.RegexAnalyzer() | analysis.IntraWordFilter() |
                  analysis.LowercaseFilter())


class SortColumn(FieldType):
    indexed = False
    stored = False
    column_type = columns.VarBytesColumn()

    def __init__(self):
        pass


def intraword(text, **kwargs):
    '''Standard analyzer that additionaly breaks camelCased words'''

    yield from normal_analyzer(text, **kwargs)
    yield from intra_analyzer(text, **kwargs)


class DB:
    def __init__(self, config, api):
        self.config = config
        self.api = api
        self.cache_dir = user_cache_dir('fac', appauthor=False)
        self.storage = FileStorage(os.path.join(self.cache_dir, 'index'))

        self.schema = Schema(
            name=TEXT(sortable=True, phrase=True, field_boost=3,
                      analyzer=intraword),
            owner=TEXT(sortable=True, field_boost=2.5,
                       analyzer=intraword),
            title=TEXT(field_boost=2.0, phrase=False),
            summary=TEXT(phrase=True),
            downloads=NUMERIC(sortable=True),
            sort_name=SortColumn(),
            name_id=ID(stored=True),
        )

        try:
            self.index = self.storage.open_index()
        except EmptyIndexError:
            self.index = None

        self.db = JSONFile(os.path.join(self.cache_dir, 'mods.json'))

    def maybe_update(self):
        if self.needs_update():
            self.update()

    def needs_update(self):
        if not self.index or not self.db.get('mods'):
            return True

        last_update = self.db.mtime
        period = int(self.config.get('db', 'update_period'))
        db_age = time.time() - last_update

        return db_age > period

    def update(self):
        with ProgressWidget("Downloading mod database...") as progress:
            mods = self.api.get_mods(progress)

        old_mods = self.db.get('mods', {})

        self.db.mods = {mod.name: mod.data
                        for mod in mods}

        if old_mods != self.db['mods']:
            print("Building search index...")
            self.index = self.storage.create().create_index(self.schema)

            with self.index.writer() as w:
                for mod in mods:
                    w.add_document(
                        name_id=mod.name,
                        name=mod.name,
                        sort_name=mod.name.lower(),
                        title=mod.title.lower(),
                        owner=mod.owner.lower(),
                        summary=mod.summary.lower(),
                        downloads=mod.downloads_count
                    )
                self.db.save()
            print("Updated mods database (%d mods)" % len(mods))
        else:
            print("Index is up to date")
            self.db.utime()

    def search(self, query, sortedby=None, limit=None):
        parser = qparser.MultifieldParser(
            ['owner', 'name', 'title', 'summary'],
            schema=self.schema
        )
        parser.add_plugin(qparser.FuzzyTermPlugin())

        if not isinstance(query, Query):
            query = parser.parse(query or 'name:*')

        with self.index.searcher() as searcher:
            if sortedby:
                facets = []
                for field in sortedby.split(','):
                    reverse = field.startswith('-')
                    if reverse:
                        field = field[1:]

                    if 'sort_' + field in self.schema:
                        field = 'sort_' + field
                    facets.append(FieldFacet(field, reverse=reverse))

                if len(facets) == 1:
                    sortedby = facets[0]
                else:
                    sortedby = MultiFacet(facets)

            for result in searcher.search(
                    query,
                    limit=limit,
                    sortedby=sortedby):

                d = JSONDict(self.db.mods[result['name_id']])
                d.score = result.score
                yield d

    @property
    def mods(self):
        return self.db.mods
