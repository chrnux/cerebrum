import forgetHTML as html
from nav.web import sci_exp

class Value(html.Text):
    """A special html-text containing a number.
       The item is sorted according to the numeric value, but 
       printed with the given decimal counts and the optional unit. 
       """
    def __init__(self, value, unit="", decimals=2, 
                 sciunit=False, **kwargs):
        try:
            _ = value + 0
            assert _ == value
        except:
            raise "Value %r not a number" % value
        self.value = value
        self.decimals = decimals
        self.unit = unit
        self.sciunit = sciunit
        html.Text.__init__(self, self._display(), **kwargs)
    def _display(self):
        format = "%0." + str(self.decimals) + "f"
        if self.sciunit:
            (value, unit) = sci_exp.sci(self.value)
            unit = unit + self.unit
        else:
            unit = self.unit
            value = self.value
        formatted = format % value
        return formatted + unit
    def __cmp__(self, other):
        if isinstance(other, html.TableCell):
            return cmp(self.value, other.value)
        else:
            return cmp(self.value, other)


class TableView(html.SimpleTable):
    def __init__(self, *headers, **kwargs):
        html.SimpleTable.__init__(self, header=None)
        self['class'] = "tableView"
        self.headers = headers
        self._width = len(headers)
        self.__kwargs = kwargs
        try:
            self.sortBy = int(kwargs.get('sortBy', 0)) # default: nosort
        except:
            self.sortBy = 0
        self.baseurl = kwargs.get('baseurl', '')
        
    def sort(self):
        def _getColumns(column, a, b):
            try:
                aValue = a[column]
            except IndexError:
                aValue = None
            try:
                bValue = b[column]
            except IndexError:
                bValue = None
            return (aValue, bValue)    

        def _sorter(a, b):
            # the column to check
            column = abs(sortBy) # remember, the first
                                 # one is kwargs..
            # find the reverse-effect
            comp = lambda x,y: sortBy/abs(sortBy) * cmp(x,y)
            # If the column is empty, it is None
            (aValue, bValue) = _getColumns(column, a, b)
            # the compared value    
            res = comp(aValue, bValue)
            if res:
                return res
            for col in range(1,len(self._items)+1):
                if col == column:
                    continue
                res = comp(*_getColumns(col, a,b))
                if res:
                    return res
            return 0            
                        
        self._content = [] # reset html version
        if self.sortBy:
            sortBy = self.sortBy
            self._items.sort(_sorter)
    def _generateContent(self):
        row = html.TableRow(**self.__kwargs)
        self.append(row)
        count = 0
        for header in self.headers:
            count += 1
            link = html.Anchor(header)
            headerCell = html.TableHeader(link)
            headerCell['class'] = "sort col%s" % count
            row.append(headerCell)
            if abs(self.sortBy) == count:
                # reverse the current
                link['href'] = '%s?sort=%s' % (self.baseurl, -self.sortBy)
                headerCell['id'] = "activeSort"
                if self.sortBy < 0:
                    headerCell['class'] = "reverseSort"
            else:
                link['href']='%s?sort=%s' % (self.baseurl, count)
        # make sure width is correct.        
        for extra in range(self._width - len(self.headers)):
            row.append(html.TableHeader(''))
        html.SimpleTable._generateContent(self)        
    def output(self, *args, **kwargs):
        return html.SimpleTable.output(self, *args, **kwargs)

