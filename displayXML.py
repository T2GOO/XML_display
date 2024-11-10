from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox
import xml.etree.ElementTree as ET

# Main window
class Display_XML(Tk):

    prev_XML_path_file = ""
    XML_path_file = ""
    columns_to_show = "name"
    info_table = {}
    nsToDisplay = {"": True}
    elementsFound = []

    def __init__(self):
        super().__init__()
        self.iconbitmap("image/icon.ico")
        self.title("Display XML")
        self.geometry("1000x800")

        # Create a frame for settings
        self.settings_frame = Frame(self, padx=10, pady=10)
        self.settings_frame.pack(fill=X)
        # Add an import file button
        import_button = ttk.Button(
            self.settings_frame, text="Import XML File", command=self.import_file
        )
        import_button.pack(padx=10, pady=10)

        self.buttonClear = ttk.Button(
            self.settings_frame, text="Clear", command=self.clear
        )
        self.buttonSettings = ttk.Button(
            self.settings_frame, text="Settings", command=self.settings
        )
        self.printNs = True
        self.checkButtonNs = ttk.Checkbutton(
            self.settings_frame,
            text="Display namespaces",
            command=self.onClickCheck,
            variable=BooleanVar(value=self.printNs),
        )
        # search bar
        self.sv = StringVar(value="@attribute=value")
        self.sv.trace_add("write",self.on_search)
        self.labelSearch = ttk.Label(self.settings_frame)
        self.entrySearch = ttk.Entry(self.settings_frame, textvariable=self.sv, width=50)
        self.entrySearch.bind("<Return>", self.go_to_next_element)
        self.buttonSearch = ttk.Button(
            self.settings_frame, text="Next", command=self.go_to_next_element
        )
        # close and open all
        self.buttonCloseAll = ttk.Button(
            self.settings_frame,
            text="Close all",
            command=lambda: self.treeElemCloser(False),
        )
        self.buttonOpenAll = ttk.Button(
            self.settings_frame, text="Open all", command=self.treeElemCloser
        )

        # Create a frame for the XML tree
        self.tree_frame = Frame(self, padx=10, pady=10)
        self.tree_frame.pack(expand=True, fill="both")

    def on_search(self, var, index, mode):
        self.search_element()
        self.set_label_search()
        
    def set_label_search(self):
        if len(self.elementsFound) != 0:
            self.labelSearch.config(text = str(len(self.elementsFound))+" found")
        else:
            self.labelSearch.config(text = "")

    def treeElemCloser(self, mOpen=True):
        for id in self.info_table.keys():
            self.treeview_file.item(id, open=mOpen)

    def go_to_next_element(self, event = ""):
        if len(self.elementsFound) != 0:
            elem_selected = False
            i = 0
            while i < len(self.elementsFound)-1 and not elem_selected:
                if self.elementsFound[i][1] == 1:
                    elem_selected = True
                    self.elementsFound[i][1] = 0
                    self.elementsFound[i+1][1] = 1
                    self.openParents(self.elementsFound[i+1][0])
                    self.treeview_file.item(self.elementsFound[i+1][0], open=True)
                    self.treeview_file.selection_set(self.elementsFound[i+1][0])
                i+=1
            if not elem_selected:
                self.elementsFound[0][1] = 1
                self.openParents(self.elementsFound[0][0])
                self.treeview_file.item(self.elementsFound[0][0], open=True)
                self.treeview_file.selection_set(self.elementsFound[0][0])

    def search_element(self, event=""):
        user_command = self.sv.get()
        # Structure command: @attribute=value
        # if start with @ -> search by one attribute
        if user_command.startswith("@"):
            attribute = user_command[1 : user_command.find("=")].strip()
            value = user_command[user_command.find("=") + 1 :].strip() if user_command.find("=") != -1 else ""
            if attribute and value:
                found, items = self.findElemByX(attribute, value, first=False)
                if found:
                    self.elementsFound = [[items[i], 0] for i in range(len(items))]
                else:
                    self.elementsFound = []
            else:
                self.elementsFound = []
        else:
            self.elementsFound = []

    def onClickCheck(self):
        # Update printNs
        self.printNs = not self.printNs
        # Destroy and display treeview
        self.explore_file()

    def import_file(self):
        filename = filedialog.askopenfilename(
            initialdir="/",
            title="Select a File",
            filetypes=(("XML files", "*.xml"), ("all files", "*.*")),
        )  # Allow "all files" to handle specific XML (e.g. ARXML, railML)
        if filename:
            self.XML_path_file = filename
            self.explore_file()

    def explore_file(self):
        # Clean the treeview
        self.tree_frame.destroy()
        # Create a frame for the XML tree
        self.tree_frame = Frame(self, padx=10, pady=10)
        self.tree_frame.pack(expand=True, fill="both")

        # Create the treeview
        self.treeview_file = ttk.Treeview(
            self.tree_frame, columns=self.columns_to_show, show="tree headings"
        )
        self.treeview_file.bind("<ButtonRelease-1>", self.on_click)
        self.treeview_file.heading("#0", text="Structure")
        self.treeview_file.heading("name", text="name")

        # Add the content to the treeview
        self.content = self.get_content(self.XML_path_file)
        if len(self.content) > 0:
            self.display()

    def clear_view(self):
        self.buttonClear.pack_forget()
        self.buttonSettings.pack_forget()
        self.checkButtonNs.pack_forget()
        self.entrySearch.pack_forget()
        self.labelSearch.pack_forget()
        self.buttonSearch.pack_forget()
        self.buttonCloseAll.pack_forget()
        self.buttonOpenAll.pack_forget()
        self.elementsFound = []
        self.sv.set("@attribute=value")
        self.info_table = {}

    def display(self):
        self.get_namespaces()
        # manage namespaces
        ns = ""
        itemNSindex = self.content.tag.find("}")
        if itemNSindex != -1:
            itemNS = self.content.tag[: itemNSindex + 1]
            ns = (
                self.namespaces[itemNS[1:-1]] + ":"
                if len(self.namespaces[itemNS[1:-1]]) > 0
                else ""
            )
            if not self.printNs:
                contentTag = self.content.tag[itemNSindex + 1 :]
            else:
                contentTag = ns + self.content.tag[itemNSindex + 1 :]
        else:
            contentTag = self.content.tag

        # unpack clear and settings
        try:
           self.clear_view()
        except:
            pass
        if self.nsToDisplay[ns]:
            id = self.treeview_file.insert(
                "", "end", text=contentTag, values=(self.content.text,)
            )
            self.info_table[id] = self.content
            self.put_content(self.content, id)
            self.treeview_file.grid(column=0, padx=10, pady=10)
            self.treeview_file.pack(
                expand=True, fill="both", padx=10, pady=10, side="left"
            )
            # Place the scrollbar on the right side of the Treeview
            scrollbar = ttk.Scrollbar(
                self.tree_frame, orient="vertical", command=self.treeview_file.yview
            )
            self.treeview_file.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="left", fill="y")
            self.display_information()

            self.buttonClear.pack(side="left", padx=10, pady=10)
            self.checkButtonNs.pack(side="left", padx=10, pady=10)
            self.buttonSearch.pack(side="right", padx=10, pady=10)
            self.entrySearch.pack(side="right", padx=10, pady=10)
            self.labelSearch.pack(side="right", padx=10, pady=10)
            self.buttonCloseAll.pack(side="left", padx=10, pady=10)
            self.buttonOpenAll.pack(side="left", padx=10, pady=10)

            # self.buttonSettings.pack(side = "left", padx=10, pady=10)

    def settings(self):
        "top level window for settings"
        top = Toplevel(self)
        top.title("Settings")
        top.geometry("300x300")

        # add a frame for namespaces to display
        namespaces_frame = Frame(top, padx=10, pady=10)
        namespaces_frame.pack()

        listNs = {}
        for k, v in self.namespaces.items():
            # print(k, v)
            mini_frame = Frame(namespaces_frame, padx=10, pady=10)
            mini_frame.pack()
            label = Label(mini_frame, text=v)
            label.pack(side="left")
            listNs[v] = BooleanVar(value=self.nsToDisplay[v + ":"])
            checkbutton = Checkbutton(mini_frame, variable=listNs[v])
            checkbutton.pack(side="right")

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
        self.prev_XML_path_file = ""
        self.clear_view()

    def get_namespaces(self):
        self.namespaces = {}
        for _, elem in ET.iterparse(self.prev_XML_path_file, events=("start-ns",)):
            ns, url = elem
            self.namespaces[url] = ns
            self.nsToDisplay[ns + ":"] = True

    def display_information(self):
        # Display the information in another treeview
        self.treeview_info = ttk.Treeview(
            self.tree_frame, columns=("value"), show="tree headings"
        )
        self.treeview_info.heading("#0", text="attribute")
        self.treeview_info.column("#0",minwidth=0, width=20)
        self.treeview_info.heading("value", text="value")
        self.treeview_info.column("value",minwidth=0, width=60)
        self.treeview_info.bind("<Button-3>", self.goToRef)
        self.treeview_info.pack(
            expand=True, fill="both", padx=10, pady=10, side="right"
        )

    def openParents(self, item):
        parent_id = self.treeview_file.parent(item)
        while parent_id:
            self.treeview_file.item(parent_id, open=True)
            parent_id = self.treeview_file.parent(parent_id)

    def goToRef(self, event):
        iid = self.treeview_info.identify_row(event.y)
        if iid:
            # mouse pointer over item
            self.treeview_info.selection_set(iid)
            ref = self.treeview_info.item(iid)["values"]
            # Try to find the ref by Id
            found, item = self.findElemByX("id", ref[0])
            if found:
                self.openParents(item)
                self.treeview_file.item(item, open=True)
                self.treeview_file.selection_set(item)
                # print(self.treeview_file.item(item))
        else:
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass

    def findElemByX(self, attribute, value, first=True):
        list_elem = []
        # print(self.info_table.items())
        # Browse infoTable
        for k, v in self.info_table.items():
            if self.getAttribute(v, attribute) == value:
                if first:
                    return True, k
                else:
                    list_elem.append(k)
        if len(list_elem) != 0:
            return True, list_elem
        else:
            return False, None

    def on_click(self, event):
        if self.treeview_file.selection():
            self.updateTreeviewInfo(self.treeview_file.selection()[0])

    def updateTreeviewInfo(self, item):
        # cleqr the treeview
        for i in self.treeview_info.get_children():
            self.treeview_info.delete(i)
        attributes = self.info_table[item].attrib
        for k, v in attributes.items():
            # remove namespaces
            key = k[k.find("}") + 1 :] if k.find("}") != -1 else k
            self.treeview_info.insert("", "end", text=key, values=v)
        txt = (
            (self.info_table[item].text).strip()
            if self.info_table[item].text is not None
            else ""
        )
        if len(txt) > 0:
            self.treeview_info.insert("", "end", text="text", values=(txt,))

    def put_content(self, child_list, parent):
        if len(child_list) == 0:
            return
        # Add the content to the treeview
        for child in child_list:
            # manage namespaces
            ns = ""
            itemNSindex = child.tag.find("}")
            if itemNSindex != -1:
                itemNS = child.tag[: itemNSindex + 1]
                ns = (
                    self.namespaces[itemNS[1:-1]] + ":"
                    if len(self.namespaces[itemNS[1:-1]]) > 0
                    else ""
                )
                if not self.printNs:
                    childTag = child.tag[itemNSindex + 1 :]
                else:
                    childTag = ns + child.tag[itemNSindex + 1 :]
            else:
                childTag = child.tag
            # print(ns)
            if self.nsToDisplay[ns]:
                id = self.treeview_file.insert(
                    parent,
                    "end",
                    text=childTag,
                    values=(self.getAttribute(child, "name"),),
                )
                self.info_table[id] = child
                if len(child) >= 1:
                    # get children of the current child
                    self.put_content(child, parent=id)

    def getAttribute(self, item, att):
        if att != "text":
            return item.attrib[att] if att in item.attrib.keys() else ""
        else:
            if item.text:
                return item.text if len(item.text) != -1 else ""
            else:
                return ""

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
                tkinter.messagebox.showerror(
                    "Error", "The file is not a valid XML file"
                )
                # Reload the previous file
                self.XML_path_file = self.prev_XML_path_file
                root = self.get_content(self.prev_XML_path_file)
        return root


# Run the program
if __name__ == "__main__":
    Display_XML().mainloop()
