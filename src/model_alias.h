// Transitional alias header to map LN-proper names to current GGIO-based model
// Switch to the SCL-generated model by redefining these macros accordingly.

#ifndef MODEL_ALIAS_H
#define MODEL_ALIAS_H

// Data attribute aliases (server-side symbols)
// Trip result (PTRC1.Tr)
#define IEDMODEL_LD0_PTRC1_Tr_stVal        IEDMODEL_GenericIO_GGIO1_SPCSO1_stVal
#define IEDMODEL_LD0_PTRC1_Tr_q            IEDMODEL_GenericIO_GGIO1_SPCSO1_q

// Breaker position (XCBR1.Pos)
#define IEDMODEL_LD0_XCBR1_Pos_stVal       IEDMODEL_GenericIO_GGIO1_SPCSO2_stVal
#define IEDMODEL_LD0_XCBR1_Pos_q           IEDMODEL_GenericIO_GGIO1_SPCSO2_q

// Overcurrent (PTOC1)
#define IEDMODEL_LD0_PTOC1_Op_stVal        IEDMODEL_GenericIO_GGIO1_SPCSO3_stVal
#define IEDMODEL_LD0_PTOC1_Op_q            IEDMODEL_GenericIO_GGIO1_SPCSO3_q
#define IEDMODEL_LD0_PTOC1_Str_stVal       IEDMODEL_GenericIO_GGIO1_SPCSO4_stVal
#define IEDMODEL_LD0_PTOC1_Str_q           IEDMODEL_GenericIO_GGIO1_SPCSO4_q

// Measurements (MMXU1)
#define IEDMODEL_LD0_MMXU1_PhV_mag_f       IEDMODEL_GenericIO_GGIO1_AnIn1_mag_f
#define IEDMODEL_LD0_MMXU1_Amp_mag_f       IEDMODEL_GenericIO_GGIO1_AnIn2_mag_f
#define IEDMODEL_LD0_MMXU1_Hz_mag_f        IEDMODEL_GenericIO_GGIO1_AnIn3_mag_f

// String object references used by HMI client (transitional mapping)
#define REF_MMXU_VOLT      "simpleIOGenericIO/GGIO1.AnIn1.mag.f"
#define REF_MMXU_CURR      "simpleIOGenericIO/GGIO1.AnIn2.mag.f"
#define REF_MMXU_FREQ      "simpleIOGenericIO/GGIO1.AnIn3.mag.f"
#define REF_PTOC_STR       "simpleIOGenericIO/GGIO1.SPCSO4.stVal"
#define REF_PTOC_OP        "simpleIOGenericIO/GGIO1.SPCSO3.stVal"
#define REF_PTRC_TR        "simpleIOGenericIO/GGIO1.SPCSO1.stVal"
#define REF_XCBR_POS       "simpleIOGenericIO/GGIO1.SPCSO2.stVal"

#endif // MODEL_ALIAS_H

