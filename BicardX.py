
import streamlit as st
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3

def img_to_txt(path):
  bicard_input= Image.open(path)
  image_array = np.array(bicard_input)

  reader = easyocr.Reader(['en'])
  result = reader.readtext(image_array, detail=0)
  return result, bicard_input


def extracted_text(texts):
  extrd_dict = {"NAME": [], "DESIGNATION": [], "COMPANY_NAME":[],"CONTACT": [], "EMAIL": [], "WEBSITE":[],
                "ADDRESS":[], "PINCODE": []}
  extrd_dict["NAME"].append(texts[0])
  extrd_dict["DESIGNATION"].append(texts[1])

  for i in range(2,len (texts)):
    if texts[i].startswith("+") or (texts[i].replace("-", "").isdigit() and '-' in texts[i]):
      extrd_dict["CONTACT"].append(texts[i])
    elif "@" in texts[i] and ".com" in texts[i]:
      extrd_dict["EMAIL"].append(texts[i])
    elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
      small= texts[i].lower()
      extrd_dict["WEBSITE"].append(small)
    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extrd_dict["PINCODE"].append(texts[i])
    elif re.match(r'^[A-Za-z]', texts[i]):
      extrd_dict["COMPANY_NAME"].append(texts[i])
    else:
      remove_colon= re.sub(r'[,;]','',texts[i])
      extrd_dict["ADDRESS"].append(remove_colon)

  for key, value in extrd_dict.items():
    if len(value)>0:
      concadenate="".join(value)
      extrd_dict[key] = [concadenate]
    else:
        value = "NA"
        extrd_dict[key] = [value]


  return extrd_dict

#streamlit
st.set_page_config(layout="wide")

st.write("# <span style='color:green'>EXTRACTING BUSINESS CARD DATA WITH OCR</span>", unsafe_allow_html=True)

with st.sidebar:
  selected_option = st.selectbox("Main Menu", ["Home", "Upload & Modifying", "Delete"])
if selected_option == "Home":
  pass

elif selected_option == "Upload & Modifying":
  
  img= st.file_uploader("Upload the Image", type= ["png","jpg","jpeg"])
  
  if img is not None:
    st.image(img, width= 300)

    txt_img, bicard_input= img_to_txt(img)
    text_dict= extracted_text(txt_img)

    if text_dict:
      st.success("Text Extracted Done")

    df= pd.DataFrame(text_dict)
    
    #Converting Image to Bytes
    Image_bytes = io. BytesIO()
    bicard_input.save(Image_bytes, format= "PNG")
    image_data = Image_bytes.getvalue()
    
    #Creating Dictionary
    data = {"IMAGE" : [image_data]}
    df1 = pd.DataFrame(data)
    
    #Concat the DataFrame
    concat_df= pd.concat([df,df1], axis=1)

    st.dataframe(concat_df)
    button1= st.button("Save",use_container_width= True)

    if button1:
      db= sqlite3.connect("bicard.db")
      mycursor= db.cursor()

      #create a table
      create_table= '''CREATE TABLE IF NOT EXISTS bicard_details(NAME VARCHAR(255),
                                                                DESIGNATION VARCHAR(255),
                                                                COMPANY_NAME VARCHAR(255),
                                                                CONTACT VARCHAR(255),
                                                                EMAIL VARCHAR(255),
                                                                WEBSITE TEXT,
                                                                ADDRESS TEXT,
                                                                PINCODE VARCHAR(255),
                                                                IMAGE TEXT)'''
      mycursor.execute(create_table)
      db.commit()

      #Insert details
      insert_query= '''INSERT INTO bicard_details(NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE, IMAGE)
                 values(?,?,?,?,?,?,?,?,?)'''

      datas= concat_df.values.tolist()[0]
      mycursor.execute(insert_query, datas)
      db.commit()
      st.success("Saved Sucessfully!")
  method= st.radio("Select the method",["None","Preview","Modify"])
  if method== "None":
    st.write()
  elif method== "Preview":
    db= sqlite3.connect("bicard.db")
    mycursor= db.cursor()
    #select query
    select_query = "SELECT * FROM bicard_details"
    mycursor.execute(select_query)
    table = mycursor.fetchall()
    db.commit()
    table_df = pd.DataFrame(table, columns= ("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "PINCODE", "IMAGE"))
    st.dataframe(table_df)
  elif method== "Modify":
    db= sqlite3.connect("bicard.db")
    mycursor= db.cursor()
    #select query
    select_query = "SELECT * FROM bicard_details"
    mycursor.execute(select_query)
    table = mycursor.fetchall()
    db.commit()
    table_df = pd.DataFrame(table, columns= ("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE", "ADDRESS", "PINCODE", "IMAGE"))
    st.dataframe(table_df)

    col1,col2= st.columns(2)
    with col1:
      selected_name= st.selectbox("Select the Name", table_df["NAME"])
      df3= table_df[table_df["NAME"]== selected_name]
      df4= df3.copy()
      
      col1,col2= st.columns(2)
      with col1:
        modify_name= st.text_input("NAME",df3["NAME"].unique()[0])
        modify_desi= st.text_input("DESIGNATION",df3["DESIGNATION"].unique()[0])
        modify_coname= st.text_input("COMPANY_NAME",df3["COMPANY_NAME"].unique()[0])
        modify_cont= st.text_input("CONTACT",df3["CONTACT"].unique()[0])
        modify_email= st.text_input("EMAIL",df3["EMAIL"].unique()[0])

        df4["NAME"]= modify_name
        df4["DESIGNATION"]= modify_desi
        df4["COMPANY_NAME"]= modify_coname
        df4["CONTACT"]= modify_cont
        df4["EMAIL"]= modify_email

      with col2:
        modify_web= st.text_input("WEBSITE",df3["WEBSITE"].unique()[0])
        modify_add= st.text_input("ADDRESS",df3["ADDRESS"].unique()[0])
        modify_pin= st.text_input("PINCODE",df3["PINCODE"].unique()[0])
        modify_img= st.text_input("IMAGE",df3["IMAGE"].unique()[0])

        df4["WEBSITE"]= modify_web
        df4["ADDRESS"]= modify_add
        df4["PINCODE"]= modify_pin
        df4["IMAGE"]= modify_img

      st.dataframe(df4)

      col1,col2= st.columns(2)
      with col1:
        button3= st.button("Modify", use_container_width= True)

        if button3:
          db= sqlite3.connect("bicard.db")
          mycursor= db.cursor()

          mycursor.execute(f'DELETE FROM bicard_details WHERE NAME= "{selected_name}"')
          db.commit()

          #Insert details
          insert_query= '''INSERT INTO bicard_details(NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, PINCODE, IMAGE)
                values(?,?,?,?,?,?,?,?,?)'''

          datas= concat_df.values.tolist()[0]
          mycursor.execute(insert_query, datas)
          db.commit()
          st.success("MODIFIED Sucessfully!")



elif selected_option == "Delete":
  
  db= sqlite3.connect("bicard.db")
  mycursor= db.cursor()
  
  col1,col2= st.columns(2)
  with col1:
    #select query
    select_query = "SELECT NAME FROM bicard_details"
    mycursor.execute(select_query)
    table1 = mycursor.fetchall()
    db.commit()
    names=[]
    for i in table1:
      names.append(i[0])

    name_select= st.selectbox("Select the names", names)
  with col2:
    #select query
    select_query = f"SELECT DESIGNATION FROM bicard_details WHERE NAME= '{name_select}'"
    mycursor.execute(select_query)
    table2 = mycursor.fetchall()
    db.commit()
    designation=[]
    for j in table2:
      designation.append(j[0])

    designation_select= st.selectbox("Select the Designation", designation)

  if name_select and designation_select:
    col1,col2,col3= st.columns(3)
    with col1:
      st.write(f"Selected Names: {name_select}")
      st.write(" ")
      st.write(" ")
      st.write(" ")
      st.write(f"Selected Designation:{designation_select}")
    with col2:
      st.write(" ")
      st.write(" ")
      st.write(" ")
      st.write(" ")

      remove= st.button("Delete", use_container_width= True)
      if remove:
        mycursor.execute(f"DELETE FROM bicard_details WHERE NAME= '{name_select}' AND DESIGNATION= '{designation_select}'")
        db.commit()

        st.success("Deleted Successfully!!!!")



  
  
  
