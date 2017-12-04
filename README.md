# Que

Slice and dice html on the command line using CSS selectors.

## Quick start

Let's say you want to grab all the links on **http://example.com/foo/bar**:

    $ que "a->href" "http://example.com/foo/bar"

Let's say that gave you 3 lines that looked like this:

    /some/url?val=1
    /some/url2?val=2
    /some/url3?val=3

Ugh, that's not very helpful, so let's modify our argument a bit:

    $ que "a->http://example.com{href}" "http://example.com/foo/bar"

Now, that will print:

    http://example.com/some/url?val=1
    http://example.com/some/url2?val=2
    http://example.com/some/url3?val=3


## Selecting

Not sure how to use CSS Selectors?

* [Beautiful Soup CSS select docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#searching-by-css-class)
* [JQuery's CSS Selector docs](http://api.jquery.com/category/selectors/)
* [Sauce Labs Tutorial](https://saucelabs.com/resources/articles/selenium-tips-css-selectors)

The selector is divided into two parts separated by `->`, the first part is the traditional selector talked about in the above links and the second part is the attributes you want to print to the screen for each match:

    $ css.selector->attribute,...

The Selector part uses [Python's string formatting syntax](https://docs.python.org/2/library/string.html#formatspec) so you can embed the attributes you want within a larger string.


## Examples

Find all the "Download" links on a page:

que has support for the the non-standard [:contains css selector](https://www.w3.org/TR/2001/CR-css3-selectors-20011113/#content-selectors)

    $ curl http://example.com | que "a:contains(Download)->href"


Select all the links with attribute `data` that starts with "foo":

    $ curl http://example.com | que "a[data|=foo]->href"


## Installation

You can use pip to install stable:

    $ pip install que

or the latest and greatest (which might be different than what's on [pypi](https://pypi.python.org/pypi/que):

    $ pip install git+https://github.com/jaymon/que#egg=que


## Notes

* If you need a way more fully featured html command line parser, try [hq](https://github.com/rbwinslow/hq).

