import json


def main():
    with open('entities.json', encoding='utf-8') as f_in:
        with open('entities-1000.json', 'w', encoding='utf-8') as f_out:
            json_in = json.load(f_in)

            dict_out = {id: {
                'label': json_in[id]['label'],
                'wikipedia': json_in[id]['wikipedia']
            } for id in list(json_in.keys())[:1000]}

            json.dump(dict_out, f_out)


if __name__ == '__main__':
    main()
