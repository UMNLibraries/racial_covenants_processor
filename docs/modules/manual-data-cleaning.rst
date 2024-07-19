How to manually map or clean up a covenant
==========================================

Once all of the steps used to process new results have been run, many covenants (ZooniverseSubject) objects will not automatically join to modern parcels. Here's how to try to make them match up.

1. Open the ZooniverseSubject list view.

2. Filter for "has racial covenant" (Yes) and "bool parcel match" (no) to find covenants that need mapping.

3. Select a ZooniverseSubject that looks potentially fixable (e.g. geo information that looks close, but not quite right)

4. Look at the individual responses at the bottom of the ZooniverseSubject page to see what different users entered, and compare to what is saved as the "Addition," "Block" and "Lot" values at the top.

5. If you see something to fix, click on the deed images to confirm that your fix is accurate.

6. Add a ManualCorrection, and enter in ONLY the values you want to change.

7. Click "save and continue editing"

8. Check to see if there are now values in the "Matching parcels" section. If yes, then at least part of the lot has matched to a modern Parcel. If not, there is either more to fix or an automatic match isn't possible.

9. Choose a "match type" value to indicate how this parcel was matched (or how it will need to be matched in the future).

10. If you need to map lots across more than one block, add ExtraParcelCandidate objects for each additional block or lot range. ONLY ONE ManualCorrection OBJECT should be added per ZooniverseSubject.

10. If you find a Parcel record that SHOULD join to this covenant, but the Parcel record has not generated appropriate join strings, you can also consider adding a ManualParcelCandidate to the matching Parcel record. This can be necessary, for example, if the needed lot information is inside the full physical description and not captured by the lot/block/addition values saved to the Parcel record. This should not be used to deal with variations that will affect many lots, for example a different spelling for the property addition. In that case, consider a SubdivisionAlternateName or PlatAlternateName. More on these decisions TK TK TK.