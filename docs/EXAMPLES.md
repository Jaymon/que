# Examples

## Grab all the links to images

I needed to grab all the linked jpegs and add the base url, this is roughly what I did:

    $ que 'a[href$=".jpg"]->https://example.com{href}' /path/to/downloaded.html
    

## Grab all the images that begin with something

I needed to grab all the images that were on the `images.example.com` subdomain, this particular site also used a lazy-load script:

    $ que 'img[data-src^="https://images"]->data-src' /path/to/downloaded.html