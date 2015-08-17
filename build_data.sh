#!/bin/bash

rm -rf mol_data/
main="mol_data"
repulse_data="projects/repulse/unix/results"

if [ -z "$1" ] ;
then
	base="mols"
else
	base="$1"
fi
mkdir -p "$main"

for molset in $(ls $base);
do
	for path in opt/{b3lyp,cam,m06hf} noopt;
	do
		echo $molset $path
		geoms=$main/$path/geoms
		geoms_out=$geoms/out
		mkdir -p $geoms_out
		geoms_mol2=$geoms/mol2
		mkdir -p $geoms_mol2
		datadir=$base/$molset

		# Build INDO input files (simple xyz format)
		# This only has to be done per opt set
		cp -f $datadir/$path/b3lyp/*.gjf $geoms
		for f in $(ls $geoms | sed -e 's/.gjf//');
		do
			# Rename all files to get rid of _TD
			mv "$geoms/$f.gjf" "$geoms/${f/_TD/}.out" 2>/dev/null;
		done

		# Remove the everything except the geometry from the gjfs
		sed -i -e '1,/^0 1$/d' -e '/^$/d' -e '/^1 /,$d' $geoms/*.out;
		mv $geoms/*.out $geoms_out/

		# Build mol2 files for use in fingerprinting
		for f in $(ls $geoms_out);
		do
                        # Create real xyz file for conversion to mol2
			# The xyz format starts with the number of atoms
			x=$(wc -l $geoms_out/$f | sed -e 's/ .*$//');
                        sed -e "1s/^/$x\n\n/" $geoms_out/$f > $geoms_mol2/$f;
		done

		for f in $(ls $geoms_mol2 | sed -e '/.mol2/d');
		do
			babel -ixyz $geoms_mol2/$f -omol2 $geoms_mol2/${f/.out/}.mol2 > /dev/null 2>&1;
		done
		rm $geoms_mol2/*.out;

		mkdir -p $main/$path/$molset

		# Collect all DFT data
		for subpath in b3lyp cam m06hf
		do
			python fileparser.py -L -f $datadir/$path/$subpath | tail -n+2 | sed -e '/^$/d' > $main/$path/$molset/$subpath.csv
			python - <<EOF
import csv
import operator

with open("$main/$path/$molset/$subpath.csv", "r") as f, open("$main/$path/$molset/$subpath.txt", "w") as f2:
    reader = csv.reader(f, delimiter=',', quotechar='"')
    sortedlist = sorted(reader, key=operator.itemgetter(1))
    for row in sortedlist:
        if len(row) and row[10] != "---":
            f2.write(' '.join(row[x] for x in (1,5,6,10)) + '\n')
EOF
		done

		# Fix to adjust the poor sorting done by `sort`
		SCRIPT="from sys import stdin, stdout; stdout.writelines(sorted(stdin, key=lambda x: x.split()[0]))"
		for f in $(ls $repulse_data/$path/$molset/indo*.txt | sed -e's/.*indo/indo/') ;
		do
			python -c "$SCRIPT" < projects/repulse/unix/results/$path/$molset/$f > $main/$path/$molset/$f ;
		done
	done
done

# Delete bad lines from repulse data
find $main -name "*.txt" | xargs -P$(nproc) sed -i -e '/Using multi/d;/100.0 100.0 100.0/d;/Repulse/d'

tar -cjf mol_data.tar.bz2 mol_data

