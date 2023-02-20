import sys, os, re, yaml
from mdfile import MdFile
from json import dumps as json_to_string

RE_MDLINK = r'(?<=\[{2})(.*?)(?=\]{2})'   # [[link]]
RE_MDLINK = r'(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)' #[name](target)
RE_MDFM = r'(?<=(\-{3}))(.*?)(?=(\-{3}))' # front matter yaml


class MdFile():

    def __init__(self, file_path, front_matter, mdlinks):
        self.uid = 0
        self.file_path = file_path
        self.front_matter = front_matter
        self.mdlinks = mdlinks

    def __str__(self):
        return f'{self.uid}: {self.file_path}, {self.front_matter}, {self.mdlinks}'

class MdParser():

    def __init__(self, target_dir):
        self.pages = []
        self.target_dir = target_dir
        self.nodes = []

    # parse markdown front matter (yaml)
    def parse_frontmatter(self, content):
        flags = re.MULTILINE + re.IGNORECASE + re.DOTALL
        fm = re.search(RE_MDFM, content, flags=flags).group(0)
        return yaml.safe_load(fm)

    # grab all the information needed from the markdown file
    def parse_md(self, file_name):
        base_name = os.path.splitext(os.path.basename(file_name))[0]

        with open(file_name, 'r') as f:
            content = f.read()
            try:
                title = self.parse_frontmatter(content)['title']
            except (KeyError,AttributeError):
                title = base_name
            try:
                description = self.parse_frontmatter(content)['description']
            except (KeyError,AttributeError):
                description = "None"
            try:
                classification = self.parse_frontmatter(content)['classification']
            except (KeyError,AttributeError):
                classification = "Unclassified"
            try:
                encryption = self.parse_frontmatter(content)['encryption']
            except (KeyError,AttributeError):
                encryption = False

            links = re.findall(RE_MDLINK, content, flags=re.MULTILINE)

        front_matter = {"title": title,
                        "description": description,
                        "classification": classification,
                        "encryption": encryption
        }
        return MdFile(file_name, front_matter, links)

    # parse all markdown files in directory and put them into nodes.
    #  Node should look like:
    # {
    #     "nodes": [
    #       {"id": "node_0", "group": 1},
    #       ...,
    #       {"id": "node_n", "group": 1}
    #       ],
    #     "links": [
    #       {"source": "node_s0", "target": "node_t0", "value": 1},
    #       ...,
    #       {"source": "node_s1", "target": "node_t1", "value": 8}
    #       ]
    # }
    def create_graph(self):
        uid = 1

        # parse each markdown file
        for subdir, dirs, files in os.walk(self.target_dir):
            for f in files:
                if f.endswith('md'):
                    path = os.path.join(subdir, f)

                    if not any(x for x in self.pages if x.file_path == path):
                        print(f"PATH: {path}")
                        md = self.parse_md(path) # Return a MdFile object
                        md.uid = uid
                        uid += 1
                        self.pages.append(md)

        # Create graph entries
        nodes = []
        links = []
        group = 0
        for page in self.pages:
            path = page.file_path

            nodes.append({"id": page.front_matter["title"], "group": group})

            for link in page.mdlinks:
                links.append({"source": page.front_matter["title"], "target": link[0], "link": link[1], "value": 0})

            group += 1

        for link in links:
            if link["target"] not in [node["id"] for node in nodes]:
                nodes.append({"id": link["target"], "group": group})

        return {"nodes": nodes, "links": links}

def main():
    target_dir = sys.argv[1]
    parser = MdParser(target_dir)
    graph = parser.create_graph()
    with open(os.path.join(target_dir, 'mdlinks.json'), 'w+') as f:
        f.write(json_to_string(graph, indent=2, default=lambda x: x.__dict__))


if __name__ == "__main__": main()
