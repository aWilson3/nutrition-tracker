"""
Created: 2021-05-02
Updated: 2021-05-03
Alex Hegeman | ahegem1@gmail.com

Create reference table for nutrient daily recommended intake (DRI) from
data sourced from the National Institute of Health (NIH)
"""
import pandas as pd
import numpy as np

def make_dict(fh, sep, reverse=False):
    """Create a dictionary out of first two fields of a delimited text file
    param:fh - file handler object
    param:sep - field delimiter
    param:reverse - boolean, tells if the second field should be the dict key
    """
    new_dict = dict()
    fh.readline()
    for line in fh:
        linesplit = line.strip().split(sep)
        if reverse == True:
            new_dict[linesplit[1]] = linesplit[0]
        else:
            new_dict[linesplit[0]] = linesplit[1]
    return new_dict

# read in DRI reference and unit lookup files
# unit lookup file is created manually using the DRI reference tables
basepath = "/Users/Alex/Documents/lifestyle/food/nutrition"

with open(basepath + "/code/dri_unit_map_tmp.txt", "r") as fh:
    dri_ref_dict = make_dict(fh, sep=',')
with open(basepath + "/code/unit_lkup.txt", "r") as fh:
    unit_dict = make_dict(fh, sep=',', reverse=True)

# replace unit text descriptions in reference file with unit codes
for unit in dri_ref_dict:
    dri_ref_dict[unit] = unit_dict.get(dri_ref_dict[unit], dri_ref_dict[unit])

# convert to data frame
dri_ref = pd.DataFrame.from_dict(dri_ref_dict, orient='index')
dri_ref.insert(loc=0, column = "name_nih", value=dri_ref.index)
dri_ref.columns = ["name_nih", "unit_cd"]
dri_ref.index = range(dri_ref.shape[0])

# ------------------------------------------------------------------------------
# read in SR Legacy nutrient reference table
# pandas was having troulbles reading in the tilde delimeter,
# so we write the file out with utf-8 encoding before reading in again
infile = basepath + "/USDA/SRC/sr28asc/NUTR_DEF.txt"
newfile = basepath + "/USDA/SRC/sr28asc/NUTR_DEF_encoded.txt"
with open(infile, 'r') as fh:
    outstring = fh.read().encode('UTF-8')
with open(newfile, 'wb') as fh:
    fh.write(outstring)

nutrient_lookup = pd.read_csv(newfile, header=None, sep='^', quotechar='~', lineterminator='\n', doublequote=False, encoding='UTF-8')
nutrient_lookup.columns = ["num", "units", "tag", "name", "num_dec", "sr_order"]

# create placeholder columns for name and unit code from NIH reference files
nutrient_lookup.insert(loc=nutrient_lookup.shape[1], column="name_nih", value=pd.Series([""]*nutrient_lookup.shape[0]))
nutrient_lookup.insert(loc=nutrient_lookup.shape[1], column="unit_cd", value=pd.Series([9999]*nutrient_lookup.shape[0]))

# add name and unit values for lipid sub-categories
# these are not included in NIH DRI ref tables
# DRI values for these, and for total fat, will probably be handled with
# a class method or similar functionality, as the only
# DRI guidence is for total and saturated fat as % of total caloric intake
nutrient_lookup.at[90,'name_nih'] = 'saturated fatty acids total'
nutrient_lookup.at[90, 'unit_cd'] = 1

nutrient_lookup.at[117,'name_nih'] = 'monounsaturated fatty acids total'
nutrient_lookup.at[117, 'unit_cd'] = 1

nutrient_lookup.at[118,'name_nih'] = 'polyunsaturated fatty acids total'
nutrient_lookup.at[118, 'unit_cd'] = 1

# add NIH DRI names and unit codes to table
for i in range(dri_ref.shape[0]):
    lkup_val_name = dri_ref.at[i, 'name_nih']
    lkup_val_unit = dri_ref.at[i, 'unit_cd']
    insert_idx = nutrient_lookup[nutrient_lookup.name.str.lower().str.contains(lkup_val_name)].index
    # if NIH DRI value does not exist in SR lookup, create new row
    if len(insert_idx) < 1:
#         print(lkup_val_name)
        next_num = nutrient_lookup.num.max() + 1
        nutrient_lookup.loc[nutrient_lookup.shape[0]] = [next_num, "", "", "", "", "", lkup_val_name, lkup_val_unit]
    elif lkup_val_name == 'fat':
        insert_idx = 1
    elif lkup_val_name == 'vitamin d':
        insert_idx = 40
    elif lkup_val_name == 'vitamin a':
        insert_idx = 33
    elif lkup_val_name == 'protein':
        insert_idx = 0
    elif lkup_val_name == 'vitamin b-12':
        insert_idx = 58
    elif lkup_val_name == 'vitamin e':
        insert_idx = 36
    elif lkup_val_name == 'folate':
        insert_idx = 57
    nutrient_lookup.at[insert_idx, 'name_nih'] = lkup_val_name
    nutrient_lookup.at[insert_idx, 'unit_cd'] = lkup_val_unit

# drop tag and sr_order values for now and shorten df name
nutrient_lkup = nutrient_lookup.drop(labels=["tag", "sr_order"], axis=1)
# convert SR units to code values
for i in range(nutrient_lkup.shape[0]):
    unit_text = nutrient_lkup.at[i, 'units']
    if unit_text.encode() == b'\xc2\xb5g':
        unit_text = 'mcg'
    nutrient_lkup.at[i, 'units'] = unit_dict.get(unit_text, unit_text)

nutrient_lkup.columns = ['id', 'unit_cd_ndb', 'name_ndb', 'num_dec', 'name_nih', 'unit_cd_nih']

# ------------------------------------------------------------------------------
# Clean NIH DRI reference table
fname_list = ['dri_elements', 'dri_vitamins', 'dri_macro']
out_data_dict = {}
for j in range(len(fname_list)):
    fname = fname_list[j]
    fpath = "/NIH/csv/{}.csv".format(fname)
    with open(basepath + fpath, 'r') as fh:
        dri = pd.read_csv(fh)

    transposed_data = {}
    for i in range(dri.shape[0]):
        # pull out single row
        dri_row = dri.iloc[i:i+1]
        # isolate and transpose numeric values
        vals = dri_row.drop(["age_min", "age_max", "age_group", "sex"], axis=1)
        vals_t = vals.transpose()
        vals_t.columns = ["value"]
        vals_t.insert(loc=0, column = "nutrient", value = list(vals_t.index))
        vals_t.index=range(vals_t.shape[0])
        # repeat categorical data for the number of numeric values
        nrows = vals_t.shape[0]
        age_min = dri_row.age_min.repeat(nrows)
        age_max = dri_row.age_max.repeat(nrows)
        age_group = dri_row.age_group.repeat(nrows)
        sex = dri_row.sex.repeat(nrows)
        # combine categorical data
        cats = pd.concat([age_min, age_max, age_group, sex], axis=1)
        cats.index = range(cats.shape[0])
        transposed_data[i] = cats.join(vals_t)

    print(len(transposed_data))
    out_data = pd.concat([transposed_data[i] for i in transposed_data], axis=0)

    print(out_data.shape)
    out_data_dict[j] = out_data

out_data_comb = pd.concat([out_data_dict[i] for i in out_data_dict], axis=0)
print(out_data_comb.shape)
print(out_data_dict[0].shape[0] + out_data_dict[1].shape[0] + out_data_dict[2].shape[0])

# ------------------------------------------------------------------------------
# join cleaned SR Legacy nutrient lookup and NIH DRI reference tables
# into final clean reference table and write to file
nutrient_ref_tmp = out_data_comb.merge(nutrient_lkup, left_on="nutrient", right_on="name_nih", how='left')
nutrient_ref_final = nutrient_ref_tmp.drop(labels=['nutrient', 'name_ndb', 'name_nih', 'num_dec', 'unit_cd_ndb'], axis=1)
nutrient_ref_final.rename(columns={'id':'nutrient_ndb_num'}, inplace=True)
nutrient_ref_final

outfile1 = basepath + "/data/prod/nutrient_lkup.txt"
outfile2 = basepath + "/data/prod/nutrient_ref_final.txt"
nutrient_lkup.to_csv(outfile1, index=False, encoding='utf-8')
nutrient_ref_final.to_csv(outfile2, index=False, encoding='utf-8')
