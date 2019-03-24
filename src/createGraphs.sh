#!/bin/bash

if [ -z $1 ]
then
	echo "No parameters"
	exit 0
fi

BASE=$1
OUTNAME="bydev/${BASE}"

BYDEV=1
if [ -z $2 ]
then
	BYDEV=0
	OUTNAME="byaction/${BASE}"
fi

mkdir -p $OUTNAME

declare -A LIST2
counter=1;
function genDOT(){
	_BF=$1
	_OUT=$2

	if [ $BYDEV -eq 0 ] 
	then
		echo "digraph G{ graph[dpi = 300; size=\"5,5\"; ratio=fill; nodesep=0.5; ranksep=1; pad=0.5; rankdir=LR;]; " >> $_OUT
		echo "node[shape=box colorscheme=\"x11\"; style=\"filled\"; fillcolor=\"white\" color=black];" >> $_OUT
	else
		echo "digraph G{ graph[dpi = 300; size=\"5,5\"; ratio=fill;]; " >> $_OUT
		echo "node[shape=point width=0.3; colorscheme=\"x11\"; style=\"filled\"; fillcolor=\"white\" color=black];" >> $_OUT
	fi
	#	echo "edge[penwidth=3; fontsize=10];" >> $_OUT
	#	echo "digraph G{ graph [ dpi = 300 ]; size=\"5,5\"; ratio=fill;" >> $_OUT
	#	echo "node[colorscheme=\"x11\"; style=\"filled\"; fillcolor=\"white\"]; rankdir=LR; " >> $_OUT
	declare -A LIST
	pl=0
	if [ -f "$_BF/mrules.log" ]
	then
		while read -r line
		do
			pl=$(($pl+1))
			if [ $pl -eq 1 ]
			then
				continue
			else
				#BY ACTION
				if [ $BYDEV -eq 0 ] 
				then
					RULE=$(echo $line|awk -F"," '{print $1}')
					ANTECEDENT=$(echo $RULE|awk -F["{","}"] '{print $2}')
					CONSEQUENT=$(echo $RULE|awk -F["{","}"] '{print $4}')
#					if [ -x ${LIST[$ANTECEDENT]} ]; then LIST[$ANTECEDENT]=$(head -${counter} devcolors.lst | tail -1) counter=$(($counter+1)); LIST2[$ANTECEDENT]=1; fi 
#					if [ -x ${LIST[$CONSEQUENT]} ]; then LIST[$CONSEQUENT]=$(head -${counter} devcolors.lst | tail -1) counter=$(($counter+1)); LIST2[$CONSEQUENT]=1; fi 
					if [ -x ${LIST[$ANTECEDENT]} ] 
					then 
						if [ -x ${LIST2[$ANTECEDENT]} ]
						then
							LIST[$ANTECEDENT]=$(head -${counter} devcolors.lst | tail -1) counter=$(($counter+1)); LIST2[$ANTECEDENT]=${LIST[$ANTECEDENT]};
							counter=$(($counter+1));
						else	
							LIST[$ANTECEDENT]=${LIST2[$ANTECEDENT]}
						fi 
					fi	
					if [ -x ${LIST[$CONSEQUENT]} ]
					then
						if [ -x ${LIST2[$CONSEQUENT]} ]
						then
							LIST[$CONSEQUENT]=$(head -${counter} devcolors.lst | tail -1) counter=$(($counter+1)); LIST2[$CONSEQUENT]=${LIST[$CONSEQUENT]};
							counter=$(($counter+1));
						else	
							LIST[$CONSEQUENT]=${LIST2[$CONSEQUENT]}
						fi 
						
					fi
					echo "\"$ANTECEDENT\"-> \"$CONSEQUENT\";" >> $_OUT
				else
				#BY DEV
					RULE=$(echo $line|awk -F"," '{print $1}')
					ANTECEDENT=$(echo $RULE|awk -F["{","}"] '{print $2}')
					CONSEQUENT=$(echo $RULE|awk -F["{","}"] '{print $4}')

					ANTDEV=$(echo $ANTECEDENT|awk -F"-" '{print $1}')
					ANTACT=$(echo $ANTECEDENT|awk -F"-" '{print $2}')
					CONDEV=$(echo $CONSEQUENT|awk -F"-" '{print $1}')
					CONACT=$(echo $CONSEQUENT|awk -F"-" '{print $2}')


					if [ -x ${LIST[$ANTDEV]} ] 
					then 
						if [ -x ${LIST2[$ANTDEV]} ]
						then
							LIST[$ANTDEV]=$(head -${counter} devcolors.lst | tail -1) 
							counter=$(($counter+1)); 
							LIST2[$ANTDEV]=${LIST[$ANTDEV]};
							counter=$(($counter+1));
						else	
							LIST[$ANTDEV]=${LIST2[$ANTDEV]}
						fi 
					fi	
					if [ -x ${LIST[$CONDEV]} ]
					then
						if [ -x ${LIST2[$CONDEV]} ]
						then
							LIST[$CONDEV]=$(head -${counter} devcolors.lst | tail -1) 
							counter=$(($counter+1)); 
							LIST2[$CONDEV]=${LIST[$CONDEV]};
							counter=$(($counter+1));
						else	
							LIST[$CONDEV]=${LIST2[$CONDEV]}
						fi 
					fi
					echo "\"$ANTDEV\"-> \"$CONDEV\"[taillabel=\"$ANTACT\"; headlabel=\"$CONACT\"; fontsize=\"6pt\"; ];" >> $_OUT
				fi			
			fi
		done < "${_BF}/mrules.log"
		pl=$(($pl - 1))
	fi
	echo "label=\"$pl pairs of states correlated\";" >> $_OUT
	echo "labelloc=\"top\";" >> $_OUT
	for k in ${!LIST[@]}
	do
		if [ "${LIST2[$k]}" == "nada" ]
		then
			continue
		else
			if [ "${LIST2[$k]}" == "nada" ]
			then 
				continue
			else
				if [ $BYDEV -eq 0 ] 
				then
					echo "\"$k\"[fillcolor=\"${LIST2[$k]}\"; label=< <b>$k</b> > ;];" >> $_OUT
				else
					#echo "\"$k\"[fillcolor=\"${LIST[$k]}\"];" >> $_OUT
					ITEMDEV=$(echo $k|awk -F"-" '{print $1}')
					echo "\"$ITEMDEV\"[fillcolor=\"${LIST[$ITEMDEV]}\"; label=< <b>$ITEMDEV</b> > ;];" >> $_OUT
				fi
			fi
		fi
	done

	for k in ${!LISTCHECK[@]}
	do
		LIST2[$k]="nada"
	done

	echo "}" >> $_OUT
	unset LIST
}

for i in $(ls -t ${BASE} -I "report.log" ) 
do
	for j in $(ls -t ${BASE}/${i}) 
	do
		echo "$BASE - $i - $j"
		genDOT $BASE/$i/$j $OUTNAME/${i}-${j}
		if [ $BYDEV -eq 1 ] 
		then
			fdp -Tjpg ./${OUTNAME}/${i}-${j} -o ./${OUTNAME}/fdp-${i}-${j}.jpg
		else
			dot -Tjpg ./${OUTNAME}/${i}-${j} -o ./${OUTNAME}/dot-${i}-${j}.jpg
		fi
		#twopi -Tjpg ./${OUTNAME}/${i}-${j} -o ./${OUTNAME}/twopi-${i}-${j}.jpg
	done
done
cp show.php ${OUTNAME}/index.php
