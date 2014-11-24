#!/bin/bash

rm -rf mol_data/
main=mol_data
mkdir -p $main

for molset in mols mols2;
do
	for path in opt/{b3lyp,cam,m06hf} noopt;
	do
		echo $molset $path
		geoms=$main/$path/geoms
		geoms_out=$geoms/out
		mkdir -p $geoms_out
		geoms_mol2=$geoms/mol2
		mkdir -p $geoms_mol2

		# Build INDO input files (simple xyz format)
		cp -f $molset/$path/b3lyp/*.gjf $geoms
		for f in `ls $geoms`;
		do
			mv "$geoms/${f}" "$geoms/${f/_TD/}" 2>/dev/null;
		done
		for f in `ls $geoms/ | sed -e 's/.gjf//'`;
		do
			mv -f "$geoms/$f.gjf" "$geoms/$f.out" 2>/dev/null;
		done
		sed -i -e '1,/^0 1$/d' -e '/^$/d' -e '/^1 /,$d' $geoms/*.out;
		mv $geoms/*.out $geoms_out/

		# Build mol2 files for use in fingerprinting
		for f in `ls $geoms_out`;
		do
			x=$(wc -l $geoms_out/$f | sed -e 's/ .*$//'); sed -e "1s/^/$x\n\n/" $geoms_out/$f > $geoms_mol2/$f;
		done

		for f in `ls $geoms_mol2 | sed -e '/.mol2/d'`;
		do
			babel -ixyz $geoms_mol2/$f -omol2 $geoms_mol2/${f/.out/}.mol2;
		done
		rm $geoms_mol2/*.out;

		if [[ "$molset" == *2 ]]
		then
			start=N
		else
			start=O
		fi

		mkdir -p $main/$path/{O,N}

		# Collect all DFT data
		for subpath in b3lyp cam m06hf
		do
			python fileparser.py -L -f $molset/$path/$subpath | tail -n+2 | sed -e '/^$/d' > $main/$path/$start/$subpath.csv
			python - <<EOF
import csv
import operator

with open("$main/$path/$start/$subpath.csv", "r") as f, open("$main/$path/$start/$subpath.txt", "w") as f2:
    reader = csv.reader(f, delimiter=',', quotechar='"')
    sortedlist = sorted(reader, key=operator.itemgetter(1))
    for row in sortedlist:
        if len(row) and row[10] != "---":
            f2.write(' '.join(row[x] for x in (1,5,6,10)) + '\n')
EOF
		done
		cp projects/repulse/unix/data/$path/indo*.txt $main/$path
	done
done
tar -cjf mol_data.tar.bz2 mol_data
