from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox
import xml.etree.ElementTree as ET

# Main window
class Display_XML(Tk):
    def __init__(self):
        self.prev_XML_path_file = ""
        self.XML_path_file = ""
        self.columns_to_show = ("text")
        self.info_table = {}
        self.nsToDisplay = {'': True}
        self.printNs = True
        super().__init__()
        self.title("Display XML")
        self.geometry("1000x800")

        # Create a frame for settings
        self.settings_frame = Frame(self, padx=10,  pady=10)
        self.settings_frame.pack(fill=X)
        # Add an import file button
        import_button = ttk.Button(self.settings_frame, text="Import XML File", command=self.import_file)
        import_button.pack(padx=10, pady=10)

        self.buttonClear = ttk.Button(self.settings_frame, text="Clear", command=self.clear)
        self.buttonSettings = ttk.Button(self.settings_frame, text="Settings", command=self.settings)

        # Create a frame for the XML tree
        self.tree_frame = Frame(self, padx=10, pady=10)
        self.tree_frame.pack(expand=True, fill="both")

    def import_file(self):
        filename = filedialog.askopenfilename(  initialdir = "/",
                                                title = "Select a File",
                                                filetypes = (("XML files","*.xml"),
                                                       ("all files","*.*"))) # Allow "all files" to handle specific XML (e.g. ARXML)
        if filename :
            self.XML_path_file = filename
            self.explore_file()
    
    def explore_file(self):
        # Clean the treeview
        self.tree_frame.destroy()
        # Create a frame for the XML tree
        self.tree_frame = Frame(self, padx=10, pady=10)
        self.tree_frame.pack(expand=True, fill="both")

        # Create the treeview
        self.treeview_file = ttk.Treeview(self.tree_frame, columns=self.columns_to_show, show="tree headings")
        self.treeview_file.bind("<ButtonRelease-1>", self.on_click)
        self.treeview_file.heading("#0", text="Structure")
        self.treeview_file.heading("text", text="Text")

        

        # Add the content to the treeview
        self.content = self.get_content(self.XML_path_file)
        if len(self.content) > 0: self.display()
            
    def display(self):
        self.get_namespaces()
        # manage namespaces
        ns = ''
        itemNSindex = self.content.tag.find("}")
        if itemNSindex != -1:
            itemNS = self.content.tag[:itemNSindex+1]
            ns = self.namespaces[itemNS[1:-1]] + '::' if len(self.namespaces[itemNS[1:-1]]) > 0 else ""
            if not self.printNs:
                contentTag = self.content.tag[itemNSindex+1:]
            else: 
                contentTag = ns + self.content.tag[itemNSindex+1:]
        else:
            contentTag = self.content.tag

        # unpack clear and settings
        try:
            self.buttonClear.pack_forget()
            self.buttonSettings.pack_forget()
        except:
            pass
        if self.nsToDisplay[ns]:
            id = self.treeview_file.insert("", "end", text=contentTag, values=(self.content.text,))
            self.info_table[id] = self.content
            self.put_content(self.content, id)
            self.treeview_file.pack(expand=True, fill="both", padx=10, pady=10, side="left")
            self.display_information()
            
            self.buttonClear.pack(side = "left", padx=10, pady=10)
            
            # self.buttonSettings.pack(side = "left", padx=10, pady=10)

    def settings(self):
        " top level window for settings "
        top = Toplevel(self)
        top.title("Settings")
        top.geometry("300x300")

        # Add a check button
        self.printNs = BooleanVar(value=self.printNs)
        checkbutton = Checkbutton(top, text="Print namespaces", variable=self.printNs)
        checkbutton.pack()

        # add a frame for namespaces to display
        namespaces_frame = Frame(top, padx=10, pady=10)
        namespaces_frame.pack()

        listNs = {}
        for k, v in self.namespaces.items():
            # print(k, v)
            mini_frame = Frame(namespaces_frame, padx=10, pady=10)
            mini_frame.pack()
            label = Label(mini_frame, text=v)
            label.pack(side='left')
            listNs[v] = BooleanVar(value=self.nsToDisplay[v + '::'])
            checkbutton = Checkbutton(mini_frame, variable=listNs[v])
            checkbutton.pack(side='right')
        
        # Add a button to save the settings
        save_button = ttk.Button(top, text="Save", command=top.destroy)
        save_button.pack()

    def saveSettings(self, userChoice):
        for k, v in userChoice.items():
            self.nsToDisplay[k] = bool(v.get())

    def clear(self):
        self.tree_frame.destroy()
        self.tree_frame = Frame(self, padx=10, pady=10)
        self.tree_frame.pack(expand=True, fill="both")
        self.buttonClear.pack_forget()
        self.buttonSettings.pack_forget()
        self.prev_XML_path_file = ""

    def get_namespaces(self):
        self.namespaces = {}
        for _, elem in ET.iterparse(self.prev_XML_path_file, events=('start-ns',)):
            ns, url = elem
            self.namespaces[url] = ns
            self.nsToDisplay[ns + '::'] = True
    
    def display_information(self):
        # Display the information in another treeview
        self.treeview_info = ttk.Treeview(self.tree_frame, columns=("value"), show="tree headings")
        self.treeview_info.heading("#0", text="attribute")
        self.treeview_info.heading("value", text="value")
        self.treeview_info.pack(expand=True, fill="both", padx=10, pady=10, side="right")

    def on_click(self, event):
        print(self.treeview_file.selection())
        item = self.treeview_file.selection()[0]
        self.updateTreeviewInfo(item)

    def updateTreeviewInfo (self, item):
        # cleqr the treeview
        for i in self.treeview_info.get_children():
            self.treeview_info.delete(i)
        attributes = self.info_table[item].attrib
        for k, v in attributes.items():
            # remove namespaces
            key = k[k.find("}") + 1:] if k.find("}") != -1 else k
            self.treeview_info.insert("", "end", text=key, values=v)
        txt = (self.info_table[item].text).strip() if self.info_table[item].text is not None else ""
        if len(txt) > 0:
            self.treeview_info.insert("", "end", text="Text", values=(txt,))
        
    def put_content(self, child_list, parent):
        if len(child_list) == 0:
            return
        # Add the content to the treeview
        for child in child_list:
            # manage namespaces
            ns = ''
            itemNSindex = child.tag.find("}")
            if itemNSindex != -1:
                itemNS = child.tag[:itemNSindex+1]
                ns = self.namespaces[itemNS[1:-1]] + '::' if len(self.namespaces[itemNS[1:-1]]) > 0 else ""
                if not self.printNs:
                    childTag = child.tag[itemNSindex+1:]
                else: 
                    childTag = ns + child.tag[itemNSindex+1:]
            else:
                childTag = child.tag
            # print(ns)
            if self.nsToDisplay[ns]:
                id = self.treeview_file.insert(parent, "end", text=childTag, values=(child.text,))
                self.info_table[id] = child
                if len(child) > 1:
                    # get children of the current child
                    self.put_content(child, parent=id)

    def get_content(self, file):
        root = ""
        # Try to open the file as a XML file
        if file:
            try:
                tree = ET.parse(file)
                root = tree.getroot()
                self.prev_XML_path_file = file
            except:
                # If the file is not a valid XML file -> display an error message in a popup window
                tkinter.messagebox.showerror("Error", "The file is not a valid XML file")
                # Reload the previous file
                root = self.get_content(self.prev_XML_path_file)
        return root

# Run the program
if __name__ == "__main__":
    Display_XML().mainloop()