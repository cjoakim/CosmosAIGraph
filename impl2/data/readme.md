# README file for the impl2/data directory

The raw downloaded IMDb *.tsv files should be put in this directory.

The various *.json files created by the wrangling process will also
be written to this directory.

Both the *.tsv and *json files in this directory are **git ignored**.

Once fully populated, the contents of this directory should look like the following:

```
PS ...\data> dir

    Directory: ...\CosmosAIGraphPrivate\impl2\data

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         4/26/2024   3:58 PM      826725520 name.basics.tsv
-a----         4/28/2024   2:31 PM     1824926809 names.json
-a----         4/28/2024   2:32 PM      117334725 names_filtered.json
-a----         4/28/2024   2:28 PM       24250881 ratings.json
-a----         4/28/2024   2:28 PM           1490 ratings_counted.json
-a----         4/29/2024   8:38 AM           2640 readme.md
-a----         4/26/2024   3:59 PM      922302209 title.basics.tsv
-a----         4/26/2024   3:59 PM     3797230375 title.principals.tsv
-a----         4/26/2024   3:59 PM       24830726 title.ratings.tsv
-a----         4/28/2024   2:32 PM       72264917 titles.json
-a----         4/28/2024   2:29 PM         117319 titles_counted.json
```