"""
Ticker Lists for Options Scanner
=================================
Russell 1000 equivalent - approximately 1000 largest US stocks by market cap.
"""

# Russell 1000 equivalent tickers (largest ~1000 US stocks)
RUSSELL_1000_TICKERS = [
    # Mega Cap (Top 50)
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH",
    "XOM", "JNJ", "JPM", "V", "PG", "MA", "AVGO", "HD", "CVX", "MRK",
    "LLY", "ABBV", "PEP", "KO", "COST", "TMO", "MCD", "WMT", "CSCO", "ACN",
    "ABT", "CRM", "BAC", "PFE", "NFLX", "AMD", "LIN", "DHR", "NKE", "DIS",
    "ORCL", "TXN", "PM", "ADBE", "WFC", "VZ", "CMCSA", "NEE", "RTX", "BMY",
    
    # Large Cap (51-200)
    "UNP", "COP", "INTC", "AMGN", "UPS", "HON", "IBM", "QCOM", "LOW", "SPGI",
    "CAT", "GE", "INTU", "DE", "BA", "SBUX", "ELV", "AMAT", "NOW", "AXP",
    "ISRG", "MS", "BKNG", "GS", "PLD", "BLK", "GILD", "LMT", "MDLZ", "ADI",
    "TJX", "REGN", "SYK", "ADP", "VRTX", "MMC", "ETN", "CB", "SCHW", "LRCX",
    "CI", "ZTS", "MO", "TMUS", "SO", "DUK", "CME", "BDX", "EOG", "NOC",
    "PGR", "BSX", "AON", "ITW", "SLB", "EQIX", "SNPS", "CSX", "MU", "KLAC",
    "ICE", "CDNS", "FI", "CL", "WM", "SHW", "MCK", "PNC", "HUM", "APD",
    "ORLY", "FCX", "MCO", "PYPL", "NSC", "USB", "MAR", "EMR", "GD", "MSI",
    "TGT", "F", "GM", "PSX", "MET", "AJG", "NXPI", "ROP", "AZO", "ECL",
    "PXD", "MCHP", "AEP", "TRV", "SRE", "OXY", "D", "CTAS", "ADSK", "PCAR",
    
    # Large Cap (201-400)
    "CCI", "AFL", "APH", "JCI", "PSA", "CARR", "TFC", "AIG", "KMB", "HLT",
    "MNST", "WELL", "AMP", "MSCI", "NEM", "O", "EW", "FTNT", "SPG", "GIS",
    "IQV", "IDXX", "CMG", "PAYX", "TEL", "ROST", "HSY", "YUM", "KDP", "EXC",
    "STZ", "DVN", "DXCM", "DLR", "HES", "BIIB", "CMI", "ED", "ADM", "WMB",
    "DD", "VRSK", "A", "OTIS", "KR", "MTD", "AME", "DOW", "XEL", "DHI",
    "HAL", "PRU", "EA", "PPG", "ALB", "WEC", "GWW", "BK", "VICI", "FAST",
    "CTVA", "KEYS", "RSG", "CBRE", "APTV", "AWK", "GLW", "ODFL", "DFS", "LHX",
    "ROK", "FANG", "ON", "EFX", "CPRT", "FTV", "ANSS", "CDW", "VMC", "EXR",
    "ACGL", "SBAC", "HPQ", "HIG", "MTB", "MLM", "DOV", "LEN", "DLTR", "ULTA",
    "WTW", "FE", "MPWR", "GPN", "RCL", "TSCO", "ALGN", "EIX", "NVR", "IR",
    "NUE", "DAL", "TTWO", "FLT", "CAH", "EBAY", "BAX", "AVB", "ES", "CHD",
    "LUV", "BR", "TDY", "ILMN", "NTRS", "AEE", "CCL", "PPL", "STLD", "TROW",
    "EQR", "WAB", "CINF", "RF", "K", "STE", "WAT", "VTR", "HPE", "HOLX",
    "DTE", "INVH", "IRM", "PTC", "CLX", "FITB", "EPAM", "LYB", "ARE", "COO",
    "SWKS", "LVS", "BALL", "MOH", "MKC", "CNC", "TER", "MGM", "WDC", "CTRA",
    "DGX", "PKI", "EXPD", "MAA", "UAL", "HBAN", "CFG", "SYF", "TRMB", "ATO",
    "DRI", "BBY", "EXPE", "ZBRA", "WRB", "CNP", "J", "KEY", "TXT", "FDS",
    "IEX", "IT", "PODD", "SEDG", "ENPH", "MAS", "OMC", "BRO", "RJF", "TYL",
    "ESS", "POOL", "VTRS", "LKQ", "LDOS", "NTAP", "WY", "GRMN", "AKAM", "STT",
    "GPC", "HRL", "IP", "KMX", "AVY", "SWK", "JBHT", "PFG", "JKHY", "BIO",
    
    # Mid-Large Cap (401-600)
    "CE", "AES", "TECH", "NI", "CFE", "HST", "UDR", "CMS", "EVRG", "CPT",
    "LNT", "BWA", "CHRW", "PAYC", "FFIV", "WBA", "ROL", "NDAQ", "IFF", "SJM",
    "RHI", "L", "CBOE", "TPR", "PEAK", "TFX", "AIZ", "BXP", "PNR", "EMN",
    "NRG", "ALLE", "FRT", "TAP", "REG", "HII", "CRL", "NDSN", "ETSY", "PNW",
    "AOS", "HSIC", "FOXA", "FOX", "AAL", "WYNN", "GL", "CPB", "DISH", "LW",
    "MKTX", "CAG", "WHR", "BEN", "GNRC", "APA", "QRVO", "PARA", "FMC", "XRAY",
    "CZR", "DVA", "ZION", "SEE", "HAS", "VFC", "BBWI", "MHK", "NWSA", "NWS",
    "AAP", "ALK", "RKT", "RIVN", "LCID", "PLTR", "COIN", "HOOD", "RBLX", "SNOW",
    "CRWD", "ZS", "DDOG", "NET", "MDB", "PANW", "OKTA", "ZM", "DOCU", "TWLO",
    "U", "PINS", "SNAP", "LYFT", "UBER", "DASH", "ABNB", "SPOT", "SQ", "AFRM",
    "ROKU", "SHOP", "SE", "MELI", "NU", "GRAB", "CPNG", "BABA", "JD", "PDD",
    "BIDU", "NIO", "XPEV", "LI", "TME", "BILI", "IQ", "VIPS", "ZTO", "YUMC",
    "WIX", "FVRR", "ETSY", "CHWY", "W", "CVNA", "OPEN", "RDFN", "Z", "ZG",
    "PTON", "CHGG", "UPST", "SOFI", "LMND", "ROOT", "OSCR", "AMWL", "TDOC", "HIMS",
    "PATH", "CFLT", "ESTC", "SUMO", "NEWR", "DT", "FROG", "RPD", "TENB", "QLYS",
    "VRNS", "SAIL", "CYBR", "FTNT", "CRWD", "S", "ZS", "OKTA", "SAIL", "TENB",
    
    # Mid Cap (601-800)
    "GPS", "HBI", "KSS", "M", "JWN", "ANF", "URBN", "AEO", "EXPR", "BBBY",
    "GME", "AMC", "SPCE", "NKLA", "RIDE", "WKHS", "FSR", "ARVL", "REE", "GOEV",
    "QS", "MVST", "DCRC", "SNPR", "THCB", "ACTC", "CCIV", "PSTH", "IPOF", "CLOV",
    "WISH", "SDC", "BODY", "BARK", "PRPL", "LOVE", "BIRD", "IRNT", "OPAD", "TMC",
    "GENI", "DKNG", "PENN", "RSI", "BETZ", "SKLZ", "GNOG", "AGS", "SRAD", "BYD",
    "MGM", "WYNN", "CZR", "LVS", "RRR", "MLCO", "BALY", "GDEN", "CHDN", "MTN",
    "SIX", "FUN", "SEAS", "PLNT", "XPOF", "HLT", "MAR", "H", "WH", "CHH",
    "VAC", "TNL", "WYND", "IHG", "ABNB", "BKNG", "EXPE", "TRIP", "TRVG", "MMYT",
    "DESP", "LIND", "RCL", "CCL", "NCLH", "LUV", "DAL", "UAL", "AAL", "JBLU",
    "ALK", "SAVE", "HA", "ALGT", "SKYW", "MESA", "RYAAY", "AZUL", "CPA", "GOL",
    "VLRS", "AC", "ALGT", "SNCY", "ULCC", "ACHR", "JOBY", "LILM", "EVTL", "BLDE",
    "HYZN", "PLUG", "FCEL", "BE", "BLDP", "HYLN", "XL", "NKLA", "FSR", "RIVN",
    "LCID", "PTRA", "LEV", "GIK", "RIDE", "WKHS", "GOEV", "ARVL", "REE", "ELMS",
    "SOLO", "AYRO", "CENN", "MULN", "FFIE", "PSNY", "VFS", "GGPI", "POLESTAR", "LFG",
    "CLF", "X", "NUE", "STLD", "RS", "ATI", "CMC", "ZEUS", "SCHN", "SKY",
    "MLM", "VMC", "EXP", "ITE", "MDU", "USLM", "ROCK", "SUM", "CRH", "MYTE",
    
    # Mid Cap (801-1000)
    "FCX", "SCCO", "TECK", "RIO", "BHP", "VALE", "AA", "CENX", "ACH", "ARNC",
    "KALU", "CSTM", "ATI", "HXL", "TKR", "WWD", "CRS", "HAYN", "MTRN", "PRLB",
    "MOS", "NTR", "CF", "IPI", "SMG", "FMC", "CTVA", "CC", "OLN", "TROX",
    "KRON", "KRO", "HUN", "WLK", "LYB", "DOW", "DD", "EMN", "CE", "ASH",
    "ALB", "LTHM", "SQM", "LAC", "PLL", "LIVENT", "MP", "UUUU", "DNN", "NXE",
    "CCJ", "UEC", "UROY", "DNN", "URG", "URA", "NLR", "URNM", "SRUUF", "BNNLF",
    "BWXT", "TDG", "HEI", "HEI-A", "AXON", "TDY", "HII", "GD", "LMT", "NOC",
    "RTX", "BA", "LHX", "AIR", "TXT", "MRCY", "KTOS", "RKLB", "SPCE", "ASTR",
    "RDW", "MNTS", "BKSY", "PL", "IRDM", "GSAT", "ASTS", "RDW", "SPIR", "VORB",
    "LLAP", "SATL", "TSAT", "CMTL", "VSAT", "GILT", "DISH", "SATS", "MAXR", "LORL",
    "CAR", "HTZ", "UHAL", "R", "PAG", "ABG", "AN", "SAH", "LAD", "SFL",
    "GPI", "RUSHA", "PENSKE", "CRMT", "CVNA", "VRM", "LOTZ", "KMX", "CPRT", "IAA",
    "ACV", "MUSA", "CACC", "ALLY", "SC", "SAN", "QFIN", "LU", "FINV", "YRD",
    "TIGR", "FUTU", "UP", "HOOD", "IBKR", "SCHW", "AMTD", "ETFC", "LPLA", "RJF",
    "SF", "EVR", "PJT", "MC", "HLI", "GHL", "LAZ", "MOELIS", "PWP", "CG",
    "KKR", "BX", "APO", "ARES", "OWL", "BAM", "BN", "IVZ", "TROW", "BEN",
    "WDR", "VCTR", "AMG", "EV", "FHI", "CNS", "VRTS", "AB", "JHG", "APAM",
    "HLNE", "STEP", "TPG", "RVNC", "GCMG", "PTMN", "DBRG", "TWO", "NLY", "AGNC",
]

# S&P 500 subset (original list for reference/fallback)
SP500_TICKERS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "ADP", "AIG", "AMAT", "AMD", "AMGN",
    "AMZN", "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "C",
    "CAT", "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS",
    "CVX", "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX",
    "GD", "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM",
    "INTC", "INTU", "ISRG", "JNJ", "JPM", "KO", "LIN", "LLY", "LMT", "LOW",
    "MA", "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS",
    "MSFT", "NEE", "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG",
    "PM", "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT",
    "TJX", "TMO", "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V",
    "VZ", "WBA", "WFC", "WMT", "XOM"
]


def get_ticker_list(list_name="russell1000"):
    """
    Get a ticker list by name.
    
    Args:
        list_name: "russell1000" or "sp500"
    
    Returns:
        List of ticker symbols
    """
    if list_name.lower() == "sp500":
        return SP500_TICKERS.copy()
    else:
        return RUSSELL_1000_TICKERS.copy()
