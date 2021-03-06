#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

// ABSOLUTELY UNSAFE
void deserialize_buffer(const uint8_t *in, uint16_t *out) {
	// for each block of 16 channels inputted (advance by 32 on 'in' and by 16
	// on 'out'
	for (unsigned int i = 0; i < 983040; i++) {
		// for each chunk of 4 bytes corresponding to one pair of channels
		for (unsigned int j = 0; j < 8; j++) {
			// uint16_t * const outp = out + 16 * i + j;
			uint16_t * const outp = out + 16 * i + (j + 1) % 8;
			uint16_t out1 = 0, out2 = 0;
			// for each byte:
			for (unsigned int k = 0; k < 4; k++) {
				uint8_t byte = in[32 * i + 4 * j + k];
				out1 |= (((byte & 0x80) >> 4) | ((byte & 0x40) << 1) | ((byte & 0x20) << 6) | ((byte & 0x10) << 11)) >> k;
				out2 |= (((byte & 0x8)     ) | ((byte & 0x4) << 5) | ((byte & 0x2) << 10) | ((byte & 0x1) << 15)) >> k;
			}
			*outp = out1;
			*(outp + 8) = out2;
		}
	}
}
/* Need to rearrange:
 * column 7 --> column 0
 * column 15 --> column 8 (replacing column 7)
 */

int main(int argc, char *argv[]) {
	static uint8_t in[0x1E00000];
	static uint16_t out[0xF00000];
	if (argc > 2) {
		FILE *f = fopen(argv[1], "r");
		size_t result = fread(in, 1, 0x1E00000, f);
		if (ferror(f)) {
			perror("Error reading file");
			return 2;
		}
		else if (result != 0x1E00000) {
			puts("Somehow didn't read whole file");
			return 3;
		}
		else {
			fclose(f);
			puts("Starting deserialization . . .");
			deserialize_buffer(in, out);
			puts("Done deserializing!");
			FILE *fout = fopen(argv[2], "w");
			fwrite(out, 2, 0xF00000, fout);
			fclose(fout);
			return 0;
		}
	}
	else {
		printf("Usage: %s infile outfile\n", argv[0]);
		return 0;
	}
}

/*
int main(int argc, char *argv[]) {
	static uint8_t in[0x1E00000];
	static uint16_t out[0xF00000];
	if (argc > 2) {
		uint8_t *in = malloc(0x1E00000);
		if (in) {
			FILE *f = fopen(argv[1], "r");
			size_t result = fread(in, 1, 0x1E00000, f);
			if (ferror(f)) {
				perror("Error reading file");
				return 2;
			}
			else if (result != 0x1E00000) {
				puts("Somehow didn't read whole file");
				return 3;
			}
			else {
				fclose(f);
				uint16_t *out = malloc(0x1E00000);
				if (!out) {
					puts("Unable to allocate memory for out");
					return 1;
				}
				puts("Starting deserialization . . .");
				deserialize_buffer(in, out);
				puts("Done deserializing!");
				free(in);
				FILE *fout = fopen(argv[2], "w");
				fwrite(out, 2, 0xF00000, fout);
				fclose(fout);
				free(out);
				return 0;
			}
		}
		else {
			puts("Unable to allocate memory");
			return 1;
		}
	}
	else {
		printf("Usage: %s infile outfile\n", argv[0]);
		return 0;
	}
}
*/
