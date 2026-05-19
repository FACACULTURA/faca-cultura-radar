import React from "react";
import { SafeAreaView, StyleSheet } from "react-native";
import FcultFooter from "./FcultFooter";
import FcultHeader from "./FcultHeader";
import FcultScroll from "./FcultScroll";
import FcultVeil from "./FcultVeil";

type HeaderType = "H1" | "H2" | "H3" | "H4";

type Props = {
  children: React.ReactNode;
  headerType?: HeaderType;
  footer?: boolean;
  veilTop?: boolean;
  veilBottom?: boolean;
  scroll?: boolean;
  favoriteItem?: any;
  favoriteCategoria?: any;
};

export default function FcultScreen({
  children,
  headerType = "H3",
  footer = true,
  veilTop = true,
  veilBottom = true,
  scroll = true,
  favoriteItem,
  favoriteCategoria,
}: Props) {
  return (
    <SafeAreaView style={styles.container}>
      <FcultHeader
        type={headerType}
        favoriteItem={favoriteItem}
        favoriteCategoria={favoriteCategoria}
      />

      {veilTop && <FcultVeil top />}

      {scroll ? (
        <FcultScroll>
          {children}
          {footer && <FcultFooter />}
        </FcultScroll>
      ) : (
        <>
          {children}
          {footer && <FcultFooter />}
        </>
      )}

      {veilBottom && <FcultVeil bottom />}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F4F1F8",
  },
});