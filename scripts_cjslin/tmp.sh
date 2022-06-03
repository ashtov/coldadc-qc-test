for ch in $(seq 1 16); do
    python3 calc_linearity_sine.py "gui_ch${ch}.txt"
    mv temp.png temp${ch}_14bit.png
done
