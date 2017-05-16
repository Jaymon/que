# Que

Slice and dice html on the command line using CSS selectors.

## Example

Let's say you want to grab all the links on **http://example.com/foo/bar**:

    $ curl http://example.com/foo/bar | que "a->href"

Let's say that gave you 3 lines that looked like this:

    /some/url?val=1
    /some/url2?val=2
    /some/url3?val=3

Ugh, that's not very helpful, so let's modify our selection:

    $ curl http://example.com/foo/bar | que "a->http://example.com{href}"

Now, that will print:

    http://example.com/some/url?val=1
    http://example.com/some/url2?val=2
    http://example.com/some/url3?val=3


## Selecting

Not sure how to use CSS Selectors?

* [Beautiful Soup CSS select docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#searching-by-css-class)
* [JQuery's CSS Selector docs](http://api.jquery.com/category/selectors/)

The selector is divided into two parts separated by `->`, the first part is the traditional selector talked about in the above links and the second part is the attributes you want to print to the screen for each match:

    $ css.selector->attribute,selector

The Selector part can use 

## Notes

* If you need a way more fully featured html command line parser, try [hq](https://github.com/rbwinslow/hq).

