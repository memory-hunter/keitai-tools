import sys
import os

def edit(file):
    try:
        lines = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            newlines = []
            for line in lines:
                if "midlet-jar-url:" in line.lower():
                    newlines.append("MIDlet-Jar-URL: " + file.split('.')[0].split('\\')[-1] + ".jar\n")
                else:
                    newlines.append(line)
        os.remove(file)
        with open(file.split('.')[0] + ".jad", 'w', encoding='utf-8') as fr:
            fr.writelines(newlines)
        print("Processed " + file)
    except Exception as e:
        print("Error processing " + file + ". Reason : " + str(getattr(e, 'message', str(e))))
            
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python mexaedit.py dir_where_jads_and_jars_are")
    else:
        files = [f for f in os.listdir(sys.argv[1]) if f.find(".jad") != -1]
        for file in files:
            edit(os.path.join(sys.argv[1], file))